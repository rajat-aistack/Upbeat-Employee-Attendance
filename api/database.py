"""
Database connection and session management (synchronous).
Designed for easy migration from SQLite to PostgreSQL/MySQL.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from api.config import DATABASE_URL

# Convert async URL to sync if needed
SYNC_DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite", "sqlite").replace("+aiosqlite", "")

# Create synchronous engine
engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},  # Required for SQLite
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Create all tables on startup."""
    from api.models import Employee, Device, Attendance, OfficeSettings, AdminUser  # noqa
    Base.metadata.create_all(bind=engine)


def close_db():
    """Dispose engine on shutdown."""
    engine.dispose()
