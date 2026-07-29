"""
SQLAlchemy database models for SRE health monitoring and auditing.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class User(Base):
    """
    SQLAlchemy model representing system users with specific roles (Admin, Operator, Viewer).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="Viewer", nullable=False)  # Admin, Operator, Viewer
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

class Service(Base):
    """
    SQLAlchemy model representing a monitored microservice or TCP node.
    """
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    environment = Column(String(30), nullable=False)  # Development, Testing, Production
    health_url = Column(String(255), nullable=False)  # HTTP URL or host:port
    ip_address = Column(String(45), nullable=False)
    port = Column(Integer, nullable=False)
    
    # Alert thresholds
    response_time_threshold = Column(Integer, default=1000, nullable=False)  # in ms
    cpu_threshold = Column(Float, default=90.0, nullable=False)             # in %
    memory_threshold = Column(Float, default=90.0, nullable=False)          # in %

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    health_logs = relationship("HealthLog", back_populates="service", cascade="all, delete-orphan")

class HealthLog(Base):
    """
    SQLAlchemy model representing the results of a service health probe check.
    """
    __tablename__ = "health_logs"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    status = Column(String(20), nullable=False)  # Healthy, Warning, Critical, Offline, Unknown
    response_time = Column(Float, default=0.0, nullable=False)  # Latency in ms
    http_status = Column(Integer, nullable=True)  # e.g., 200, 500
    remarks = Column(Text, nullable=True)         # Errors or extra context
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    service = relationship("Service", back_populates="health_logs")

class AuditLog(Base):
    """
    SQLAlchemy model tracking operator actions (e.g. login, service adjustments).
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # Login, Service Created, etc.
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
