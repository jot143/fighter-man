#!/usr/bin/env python3
"""Firefighter Server - Socket.IO + REST API for sensor data collection.

Receives sensor data from Raspberry Pi via Socket.IO and stores in Qdrant.
Provides REST API for session management and data export.
"""

import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS

from lib.config import Config
from lib.vector_store import VectorStore

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
config = Config.from_env()
app.config["SECRET_KEY"] = config.server.secret_key

# Enable CORS
CORS(app)

# Initialize Socket.IO
# Using threading mode for development stability
# For production with high concurrency, use gevent or eventlet
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    logger=False,
    engineio_logger=False,
)

# Initialize Qdrant vector store
vector_store: VectorStore = None

# Session management
sessions = {}  # session_id -> session_info
current_session_id: str = None


def get_vector_store() -> VectorStore:
    """Get or create vector store instance."""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore(config.qdrant)
    return vector_store


# ============================================================
# Socket.IO Event Handlers
# ============================================================

@socketio.on("connect", namespace="/iot")
def handle_connect():
    """Handle client connection."""
    print(f"[Socket.IO] Client connected: {request.sid}")


@socketio.on("disconnect", namespace="/iot")
def handle_disconnect():
    """Handle client disconnection."""
    print(f"[Socket.IO] Client disconnected: {request.sid}")


@socketio.on("authenticate", namespace="/iot")
def handle_authenticate(data):
    """
    Handle device authentication.

    Expected data: {"device_key": "firefighter_pi_001"}
    """
    device_key = data.get("device_key", "")

    if config.auth.is_valid_device(device_key):
        print(f"[Socket.IO] Device authenticated: {device_key}")
        emit("auth_success", {"device_key": device_key, "session_id": current_session_id})
    else:
        print(f"[Socket.IO] Authentication failed: {device_key}")
        emit("auth_error", {"message": "Invalid device key"})
        disconnect()


@socketio.on("foot_pressure_data", namespace="/iot")
def handle_foot_data(data):
    """
    Handle foot pressure sensor data.

    Expected data: {
        "timestamp": "ISO datetime",
        "device": "LEFT_FOOT" or "RIGHT_FOOT",
        "data": {
            "foot": "LEFT" or "RIGHT",
            "max": float,
            "avg": float,
            "active_count": int,
            "values": [18 floats]
        }
    }
    """
    if not current_session_id:
        return  # No active session

    store = get_vector_store()
    point_id = store.add_reading(current_session_id, "foot", data)

    if point_id:
        print(f"[Qdrant] Stored foot window: {point_id}")


@socketio.on("accelerometer_data", namespace="/iot")
def handle_accel_data(data):
    """
    Handle accelerometer sensor data.

    Expected data: {
        "timestamp": "ISO datetime",
        "device": "ACCELEROMETER",
        "data": {
            "acc": {"x": float, "y": float, "z": float},
            "gyro": {"x": float, "y": float, "z": float},
            "angle": {"roll": float, "pitch": float, "yaw": float}
        }
    }
    """
    if not current_session_id:
        return  # No active session

    store = get_vector_store()
    point_id = store.add_reading(current_session_id, "accel", data)

    if point_id:
        print(f"[Qdrant] Stored accel window: {point_id}")


# ============================================================
# REST API - Health
# ============================================================

@app.route("/health", methods=["GET"])
def health_check():
    """Server health check."""
    store = get_vector_store()
    qdrant_health = store.health_check()

    return jsonify({
        "status": "healthy" if qdrant_health["status"] == "healthy" else "degraded",
        "server": "running",
        "qdrant": qdrant_health,
        "active_session": current_session_id,
    })


# ============================================================
# REST API - Sessions
# ============================================================

@app.route("/api/sessions", methods=["POST"])
def create_session():
    """
    Create a new recording session.

    Request body: {"name": "optional session name"}
    """
    global current_session_id

    data = request.get_json() or {}
    session_name = data.get("name", f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    # Flush any existing session
    if current_session_id:
        store = get_vector_store()
        store.flush_session(current_session_id)

    # Create new session
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "name": session_name,
        "created_at": datetime.now().isoformat(),
        "status": "recording",
    }
    current_session_id = session_id

    print(f"[Session] Created: {session_id} ({session_name})")

    # Notify connected clients
    socketio.emit(
        "session_started",
        {"session_id": session_id, "name": session_name},
        namespace="/iot",
    )

    return jsonify(sessions[session_id]), 201


@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    """List all sessions."""
    return jsonify(list(sessions.values()))


@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    """Get session details."""
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    store = get_vector_store()
    windows = store.get_session_data(session_id, include_raw=False)

    session_info = sessions[session_id].copy()
    session_info["window_count"] = len(windows)
    session_info["windows"] = windows

    return jsonify(session_info)


@app.route("/api/sessions/<session_id>", methods=["PUT"])
def update_session(session_id):
    """
    Update session (labels, name, status).

    Request body: {
        "name": "new name",
        "status": "completed",
        "labels": {"window_id": "Walking", ...}
    }
    """
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json() or {}

    # Update session metadata
    if "name" in data:
        sessions[session_id]["name"] = data["name"]
    if "status" in data:
        sessions[session_id]["status"] = data["status"]

    # Update labels in Qdrant
    if "labels" in data:
        store = get_vector_store()
        updated = store.update_labels(session_id, data["labels"])
        sessions[session_id]["labels_updated"] = updated

    return jsonify(sessions[session_id])


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    """Delete a session and all its data."""
    global current_session_id

    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    store = get_vector_store()
    deleted_count = store.delete_session(session_id)

    del sessions[session_id]

    if current_session_id == session_id:
        current_session_id = None

    return jsonify({
        "message": f"Session deleted",
        "windows_deleted": deleted_count,
    })


@app.route("/api/sessions/<session_id>/stop", methods=["POST"])
def stop_session(session_id):
    """Stop the current recording session."""
    global current_session_id

    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    # Flush remaining data
    store = get_vector_store()
    store.flush_session(session_id)

    sessions[session_id]["status"] = "stopped"
    sessions[session_id]["stopped_at"] = datetime.now().isoformat()

    if current_session_id == session_id:
        current_session_id = None

    # Notify connected clients
    socketio.emit(
        "session_stopped",
        {"session_id": session_id},
        namespace="/iot",
    )

    return jsonify(sessions[session_id])


# ============================================================
# REST API - Export
# ============================================================

@app.route("/api/sessions/<session_id>/export", methods=["GET"])
def export_session(session_id):
    """
    Export session data for annotation tool or ML training.

    Query params:
        format: "json" (default) or "csv"
        include_raw: "true" to include raw sensor data
    """
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    include_raw = request.args.get("include_raw", "false").lower() == "true"
    export_format = request.args.get("format", "json")

    store = get_vector_store()
    windows = store.get_session_data(session_id, include_raw=include_raw)

    if export_format == "csv":
        # Simple CSV export
        import csv
        from io import StringIO

        output = StringIO()
        if windows:
            fieldnames = ["id", "start_time", "end_time", "foot_count", "accel_count", "label"]
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(windows)

        response = app.response_class(
            response=output.getvalue(),
            status=200,
            mimetype="text/csv",
        )
        response.headers["Content-Disposition"] = f"attachment; filename={session_id}.csv"
        return response

    # JSON export (default)
    return jsonify({
        "session": sessions[session_id],
        "windows": windows,
        "window_count": len(windows),
    })


# ============================================================
# REST API - Query (Similarity Search)
# ============================================================

@app.route("/api/query/similar", methods=["POST"])
def query_similar():
    """
    Find similar sensor patterns.

    Request body: {
        "window_id": "id of reference window",
        "session_id": "optional filter by session",
        "label": "optional filter by label",
        "limit": 10
    }
    """
    data = request.get_json() or {}
    window_id = data.get("window_id")
    session_filter = data.get("session_id")
    label_filter = data.get("label")
    limit = data.get("limit", 10)

    if not window_id:
        return jsonify({"error": "window_id is required"}), 400

    store = get_vector_store()

    # Get the reference window's vector
    try:
        points = store.client.retrieve(
            collection_name=store.config.collection,
            ids=[window_id],
            with_vectors=True,
        )
        if not points:
            return jsonify({"error": "Window not found"}), 404

        reference_vector = points[0].vector
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Search for similar
    results = store.query_similar(
        vector=reference_vector,
        limit=limit + 1,  # +1 because result may include the reference
        session_id=session_filter,
        label=label_filter,
    )

    # Remove the reference window from results
    results = [r for r in results if r["id"] != window_id][:limit]

    return jsonify({
        "reference_id": window_id,
        "similar_windows": results,
    })


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Firefighter Server")
    print("=" * 60)
    print(f"Host: {config.server.host}")
    print(f"Port: {config.server.port}")
    print(f"Debug: {config.server.debug}")
    print(f"Qdrant: {config.qdrant.host}:{config.qdrant.port}")
    print("=" * 60)

    # Initialize vector store on startup
    get_vector_store()

    socketio.run(
        app,
        host=config.server.host,
        port=config.server.port,
        debug=config.server.debug,
        allow_unsafe_werkzeug=True,  # Required for threading mode in development
    )
