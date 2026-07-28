"""
Database configuration and session management.

This module configures the SQLAlchemy database engine and session maker,
supporting SQLite for local development and PostgreSQL for production environments.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.session import Session

# Default to SQLite for local development, support PostgreSQL via env variable
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./health.db")

# SQLite requires 'check_same_thread: False' to allow multi-threading in FastAPI
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Normalise legacy 'postgres://' connection strings (e.g. from Heroku/Render)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Initialize database engine and session factory
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base model class
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.
    
    Ensures that the database session is closed after the request is finished.
    Yields:
        Session: The active database transaction session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
