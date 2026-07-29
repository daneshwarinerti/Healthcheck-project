"""
Database configuration and session management for the Monitoring Dashboard.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.session import Session

# Default to SQLite for local development, support PostgreSQL via env variable
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./health.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Normalize legacy postgres connection string scheme
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Yields database transaction sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
