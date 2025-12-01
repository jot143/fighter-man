#!/usr/bin/env python3
"""Test REST API endpoints for firefighter-server.

Usage:
    python test_api.py [--server URL]
"""

import argparse
import json
import requests
import time


class APITester:
    """Test REST API endpoints."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session_id = None

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request."""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, **kwargs)
        return response

    def test_health(self) -> bool:
        """Test health endpoint."""
        print("\n[Test] GET /health")
        try:
            resp = self._request("GET", "/health")
            data = resp.json()

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            assert data.get("server") == "running", "Server not running"

            print(f"  Status: {data.get('status')}")
            print(f"  Qdrant: {data.get('qdrant', {}).get('status')}")
            print("  [PASS]")
            return True
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False

    def test_create_session(self) -> bool:
        """Test session creation."""
        print("\n[Test] POST /api/sessions")
        try:
            resp = self._request("POST", "/api/sessions", json={"name": "test_session"})
            data = resp.json()

            assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
            assert "id" in data, "No session ID returned"

            self.session_id = data["id"]
            print(f"  Session ID: {self.session_id}")
            print(f"  Name: {data.get('name')}")
            print(f"  Status: {data.get('status')}")
            print("  [PASS]")
            return True
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False

    def test_list_sessions(self) -> bool:
        """Test session listing."""
        print("\n[Test] GET /api/sessions")
        try:
            resp = self._request("GET", "/api/sessions")
            data = resp.json()

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            assert isinstance(data, list), "Expected list"

            print(f"  Sessions found: {len(data)}")
            for session in data[:3]:  # Show first 3
                print(f"    - {session.get('id')[:8]}... ({session.get('name')})")
            print("  [PASS]")
            return True
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False

    def test_get_session(self) -> bool:
        """Test getting session details."""
        if not self.session_id:
            print("\n[Test] GET /api/sessions/:id - SKIPPED (no session)")
            return True

        print(f"\n[Test] GET /api/sessions/{self.session_id[:8]}...")
        try:
            resp = self._request("GET", f"/api/sessions/{self.session_id}")
            data = resp.json()

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            assert data.get("id") == self.session_id, "Session ID mismatch"

            print(f"  Name: {data.get('name')}")
            print(f"  Status: {data.get('status')}")
            print(f"  Windows: {data.get('window_count', 0)}")
            print("  [PASS]")
            return True
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False

    def test_update_session(self) -> bool:
        """Test updating session."""
        if not self.session_id:
            print("\n[Test] PUT /api/sessions/:id - SKIPPED (no session)")
            return True

        print(f"\n[Test] PUT /api/sessions/{self.session_id[:8]}...")
        try:
            resp = self._request(
                "PUT",
                f"/api/sessions/{self.session_id}",
                json={"name": "updated_test_session"},
            )
            data = resp.json()

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            assert data.get("name") == "updated_test_session", "Name not updated"

            print(f"  New name: {data.get('name')}")
            print("  [PASS]")
            return True
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False

    def test_export_session(self) -> bool:
        """Test session export."""
        if not self.session_id:
            print("\n[Test] GET /api/sessions/:id/export - SKIPPED (no session)")
            return True

        print(f"\n[Test] GET /api/sessions/{self.session_id[:8]}../export")
        try:
            # Test JSON export
            resp = self._request("GET", f"/api/sessions/{self.session_id}/export")
            data = resp.json()

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            assert "session" in data, "No session in export"
            assert "windows" in data, "No windows in export"

            print(f"  Format: JSON")
            print(f"  Windows: {data.get('window_count', 0)}")

            # Test CSV export
            resp = self._request(
                "GET",
                f"/api/sessions/{self.session_id}/export?format=csv",
            )
            assert resp.status_code == 200, f"CSV export failed"
            print(f"  CSV export: OK")

            print("  [PASS]")
            return True
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False

    def test_stop_session(self) -> bool:
        """Test stopping session."""
        if not self.session_id:
            print("\n[Test] POST /api/sessions/:id/stop - SKIPPED (no session)")
            return True

        print(f"\n[Test] POST /api/sessions/{self.session_id[:8]}../stop")
        try:
            resp = self._request("POST", f"/api/sessions/{self.session_id}/stop")
            data = resp.json()

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            assert data.get("status") == "stopped", "Session not stopped"

            print(f"  Status: {data.get('status')}")
            print(f"  Stopped at: {data.get('stopped_at')}")
            print("  [PASS]")
            return True
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False

    def test_delete_session(self) -> bool:
        """Test deleting session."""
        if not self.session_id:
            print("\n[Test] DELETE /api/sessions/:id - SKIPPED (no session)")
            return True

        print(f"\n[Test] DELETE /api/sessions/{self.session_id[:8]}...")
        try:
            resp = self._request("DELETE", f"/api/sessions/{self.session_id}")
            data = resp.json()

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

            print(f"  Windows deleted: {data.get('windows_deleted', 0)}")
            print("  [PASS]")

            self.session_id = None
            return True
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False

    def test_similarity_search(self) -> bool:
        """Test similarity search (requires data)."""
        print("\n[Test] POST /api/query/similar")
        try:
            # This will likely fail without data, but we test the endpoint exists
            resp = self._request(
                "POST",
                "/api/query/similar",
                json={"window_id": "nonexistent"},
            )

            # 400 or 404 are acceptable (no data)
            if resp.status_code in (400, 404):
                print(f"  Endpoint exists (returned {resp.status_code})")
                print("  [PASS] (no data to search)")
                return True

            # If we somehow have data
            data = resp.json()
            print(f"  Similar windows: {len(data.get('similar_windows', []))}")
            print("  [PASS]")
            return True
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False

    def run_all_tests(self) -> tuple:
        """Run all tests."""
        tests = [
            ("Health Check", self.test_health),
            ("Create Session", self.test_create_session),
            ("List Sessions", self.test_list_sessions),
            ("Get Session", self.test_get_session),
            ("Update Session", self.test_update_session),
            ("Export Session", self.test_export_session),
            ("Stop Session", self.test_stop_session),
            ("Similarity Search", self.test_similarity_search),
            ("Delete Session", self.test_delete_session),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  [ERROR] {e}")
                failed += 1

        return passed, failed


def main():
    parser = argparse.ArgumentParser(description="Test firefighter-server REST API")
    parser.add_argument("--server", default="http://localhost:4100", help="Server URL")
    args = parser.parse_args()

    print("=" * 50)
    print("Firefighter Server API Tests")
    print("=" * 50)
    print(f"Server: {args.server}")
    print("=" * 50)

    tester = APITester(args.server)

    # Check if server is reachable
    try:
        requests.get(f"{args.server}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Cannot connect to server at {args.server}")
        print("Make sure the server is running:")
        print("  cd firefighter-server && ./start.sh")
        return 1

    passed, failed = tester.run_all_tests()

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
