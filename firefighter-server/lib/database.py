"""Database models and repository for firefighter-server."""

import uuid
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, Text, Index, func, text
from sqlalchemy.orm import declarative_base, sessionmaker

from lib.config import PostgresConfig

Base = declarative_base()


class Session(Base):
    """Session model - represents a training recording session."""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    activity_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    stopped_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="recording")
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    video_file_path = Column(Text, nullable=True)
    video_duration_seconds = Column(Float, nullable=True)
    video_size_bytes = Column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_activity_type", "activity_type"),
        Index("idx_sessions_created_at", "created_at"),
        Index("idx_sessions_status_activity", "status", "activity_type"),
    )

    def to_dict(self):
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "activity_type": self.activity_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "status": self.status,
            "video_file_path": self.video_file_path,
            "video_duration_seconds": self.video_duration_seconds,
            "video_size_bytes": self.video_size_bytes,
        }


class Database:
    """Database connection and session management."""

    def __init__(self, config: PostgresConfig):
        """Initialize database connection."""
        self.config = config
        self.engine = create_engine(
            config.connection_url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            echo=config.echo,
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables if they don't exist (init.sql will handle this in Docker)
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self):
        """Get database session with automatic commit/rollback."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def health_check(self):
        """Check database connection health."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return {"status": "healthy", "host": self.config.host}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class SessionRepository:
    """Repository for session database operations."""

    def __init__(self, db: Database):
        """Initialize repository with database instance."""
        self.db = db

    def create(self, name, activity_type=None, session_id=None):
        """Create new session."""
        with self.db.get_session() as db_session:
            session = Session(
                id=session_id or str(uuid.uuid4()),
                name=name,
                activity_type=activity_type,
                status="recording",
            )
            db_session.add(session)
            db_session.flush()
            db_session.refresh(session)
            # Expunge to make object available after session closes
            db_session.expunge(session)
            return session

    def get(self, session_id):
        """Get session by ID."""
        with self.db.get_session() as db_session:
            session = db_session.query(Session).filter(Session.id == session_id).first()
            if session:
                db_session.expunge(session)
            return session

    def list_all(self):
        """List all sessions ordered by creation date (newest first)."""
        with self.db.get_session() as db_session:
            sessions = db_session.query(Session).order_by(Session.created_at.desc()).all()
            for session in sessions:
                db_session.expunge(session)
            return sessions

    def get_active(self):
        """Get currently active (recording) session."""
        with self.db.get_session() as db_session:
            session = (
                db_session.query(Session)
                .filter(Session.status == "recording")
                .order_by(Session.created_at.desc())
                .first()
            )
            if session:
                db_session.expunge(session)
            return session

    def update(self, session_id, name=None, status=None, stopped_at=None,
               video_file_path=None, video_duration_seconds=None, video_size_bytes=None):
        """Update session fields."""
        with self.db.get_session() as db_session:
            session = db_session.query(Session).filter(Session.id == session_id).first()
            if not session:
                return None
            if name is not None:
                session.name = name
            if status is not None:
                session.status = status
            if stopped_at is not None:
                session.stopped_at = stopped_at
            if video_file_path is not None:
                session.video_file_path = video_file_path
            if video_duration_seconds is not None:
                session.video_duration_seconds = video_duration_seconds
            if video_size_bytes is not None:
                session.video_size_bytes = video_size_bytes
            db_session.flush()
            db_session.refresh(session)
            db_session.expunge(session)
            return session

    def delete(self, session_id):
        """Delete session by ID."""
        with self.db.get_session() as db_session:
            session = db_session.query(Session).filter(Session.id == session_id).first()
            if not session:
                return False
            db_session.delete(session)
            db_session.commit()
            return True

    def filter_by_activity(self, activity_type):
        """Get sessions by activity type."""
        with self.db.get_session() as db_session:
            return (
                db_session.query(Session)
                .filter(Session.activity_type == activity_type)
                .order_by(Session.created_at.desc())
                .all()
            )
