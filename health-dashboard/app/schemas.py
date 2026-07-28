"""
Pydantic schemas for request validation and response serialization.

This module contains schemas for Authentication and Server monitoring configurations,
including strict validators for IP addresses and server names, and schema examples.
"""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, field_validator

# ----------------------------------------------------
# User Authentication Schemas
# ----------------------------------------------------

class UserCreate(BaseModel):
    """
    Schema for creating or authenticating a user.
    """
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        description="Unique username of the admin user"
    )
    password: str = Field(
        ..., 
        min_length=4, 
        max_length=128, 
        description="Admin account password"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "admin-secure-password"
            }
        }
    )

class UserResponse(BaseModel):
    """
    Schema for user detail responses.
    """
    id: int
    username: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "admin"
            }
        }
    )

class Token(BaseModel):
    """
    Schema for authentication token responses.
    """
    access_token: str
    token_type: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )

class TokenData(BaseModel):
    """
    Schema representing validated token payload details.
    """
    username: Optional[str] = None

# ----------------------------------------------------
# Server Monitoring Schemas
# ----------------------------------------------------

class ServerBase(BaseModel):
    """
    Base properties shared across server schemas.
    """
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Unique readable server name identifier"
    )
    environment: str = Field(
        ..., 
        pattern="^(Dev|Test|Prod)$", 
        description="Target infrastructure tier (Dev, Test, Prod)"
    )
    ip_address: IPvAnyAddress = Field(
        ..., 
        description="IP Address (IPv4 or IPv6 format)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Validates that server names only contain alphanumeric characters,
        hyphens, and underscores to prevent injection or invalid filenames.
        """
        stripped = value.strip()
        if not re.match(r"^[a-zA-Z0-9\-_]+$", stripped):
            raise ValueError(
                "Server name must be alphanumeric and can only contain hyphens and underscores."
            )
        return stripped

class ServerCreate(ServerBase):
    """
    Schema for creating a new monitored server.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "API-01",
                "environment": "Prod",
                "ip_address": "10.0.0.10"
            }
        }
    )

class ServerUpdate(BaseModel):
    """
    Schema for updating server metadata or metrics.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    environment: Optional[str] = Field(None, pattern="^(Dev|Test|Prod)$")
    ip_address: Optional[IPvAnyAddress] = Field(None)
    status: Optional[str] = Field(None, pattern="^(Healthy|Warning|Critical|Offline)$")
    cpu_usage: Optional[float] = Field(None, ge=0.0, le=100.0)
    memory_usage: Optional[float] = Field(None, ge=0.0, le=100.0)
    uptime: Optional[int] = Field(None, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        stripped = value.strip()
        if not re.match(r"^[a-zA-Z0-9\-_]+$", stripped):
            raise ValueError(
                "Server name must be alphanumeric and can only contain hyphens and underscores."
            )
        return stripped

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "API-01-Backup",
                "environment": "Test",
                "ip_address": "10.0.0.12"
            }
        }
    )

class ServerResponse(BaseModel):
    """
    Schema representing a complete server object returned to clients.
    """
    id: int
    name: str
    environment: str
    ip_address: str  # Serializes IPvAnyAddress to clean string
    status: str
    cpu_usage: float
    memory_usage: float
    uptime: int
    last_checked: datetime
    created_at: datetime
    updated_at: datetime

    @field_validator("ip_address", mode="before")
    @classmethod
    def serialize_ip(cls, value):
        """
        Converts Pydantic IP objects or generic values into string format.
        """
        return str(value)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "API-01",
                "environment": "Prod",
                "ip_address": "10.0.0.10",
                "status": "Healthy",
                "cpu_usage": 24.5,
                "memory_usage": 45.2,
                "uptime": 15,
                "last_checked": "2026-07-28T20:00:00Z",
                "created_at": "2026-07-28T19:00:00Z",
                "updated_at": "2026-07-28T20:00:00Z"
            }
        }
    )

# ----------------------------------------------------
# Metrics & Dashboard Schemas
# ----------------------------------------------------

class DashboardSummary(BaseModel):
    """
    Schema for overall health metrics aggregation.
    """
    total_servers: int
    healthy_servers: int
    unhealthy_servers: int
    avg_cpu: float
    avg_memory: float

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_servers": 5,
                "healthy_servers": 4,
                "unhealthy_servers": 1,
                "avg_cpu": 38.2,
                "avg_memory": 45.7
            }
        }
    )
