"""
SQLAlchemy models for the Health Check Dashboard application.

This module defines the database tables 'users' (for admin access) and
'servers' (for tracking target server environments and metrics).
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, func
from app.database import Base

class User(Base):
    """
    SQLAlchemy model representing an administrator user.
    """
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String, unique=True, index=True, nullable=False)
    hashed_password: str = Column(String, nullable=False)
    
    # Audit timestamps
    created_at: datetime = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: datetime = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

class Server(Base):
    """
    SQLAlchemy model representing a monitored server target.
    """
    __tablename__ = "servers"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, unique=True, index=True, nullable=False)
    environment: str = Column(String, nullable=False)  # Allowed values: Dev, Test, Prod
    ip_address: str = Column(String, nullable=False)
    status: str = Column(String, default="Offline", nullable=False)  # Healthy, Warning, Critical, Offline
    cpu_usage: float = Column(Float, default=0.0, nullable=False)
    memory_usage: float = Column(Float, default=0.0, nullable=False)
    uptime: int = Column(Integer, default=0, nullable=False)  # Uptime in days
    
    # Timestamps
    last_checked: datetime = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    created_at: datetime = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: datetime = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
