"""
Database Configuration for Backend Core
SQLAlchemy setup for PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from shared.config import settings
from shared.logger import app_logger

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    app_logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    app_logger.info("Database initialized successfully")


def drop_db():
    """Drop all tables - USE WITH CAUTION!"""
    app_logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    app_logger.warning("All tables dropped")
