"""Database connection and session management."""

import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.models import Base

# Import all models to ensure they're registered with Base.metadata
from src.api.images.image_models import Image  # noqa: F401
from src.api.image_pull_sources.image_pull_source_models import ImagePullSource  # noqa: F401
from src.api.locations.location_models import Location, Spotting  # noqa: F401
from src.api.user_detections.user_detection_models import UserDetection  # noqa: F401
from src.api.users.user_models import User  # noqa: F401

# PostgreSQL database URL
# Format: postgresql://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./wildlife_camera.db",
)

# Create engine with SQLite-specific configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL query logging
        connect_args={
            "check_same_thread": False,  # Allow multi-threaded access
            "timeout": 60,  # Increase timeout for lock acquisition
        },
        pool_size=5,  # Limit pool size for SQLite
        max_overflow=10,  # Limit overflow connections
        pool_pre_ping=True,  # Test connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
    )

    # Enable WAL mode for SQLite to support better concurrent access
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set SQLite pragmas for better concurrency."""
        if DATABASE_URL.startswith("sqlite"):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=60000")  # 60 seconds
            cursor.execute(
                "PRAGMA synchronous=NORMAL"
            )  # Faster writes, still safe with WAL
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
            cursor.execute("PRAGMA temp_store=MEMORY")  # Keep temp tables in memory
            cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,  # Verify connections before using them
        pool_size=10,  # Number of connections to maintain
        max_overflow=20,  # Maximum number of connections beyond pool_size
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
