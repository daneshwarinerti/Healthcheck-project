"""
Pydantic schemas for service monitoring targets and Grafana-like state outputs.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ServiceBase(BaseModel):
    """
    Base properties for service targets.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Unique service identifier")
    description: Optional[str] = Field(None, max_length=500, description="Brief descriptive summary")
    environment: str = Field(..., pattern="^(Development|Testing|Production)$", description="Target environment tier")
    health_url: str = Field(..., description="HTTP health url (http://...) or host:port TCP address (e.g. localhost:5432)")
    
    # Custom SRE thresholds
    response_time_threshold: int = Field(1000, ge=10, le=30000, description="Latency limit in ms before Critical status")
    cpu_threshold: float = Field(90.0, ge=0.0, le=100.0, description="CPU alert threshold limit")
    memory_threshold: float = Field(90.0, ge=0.0, le=100.0, description="Memory alert threshold limit")

    @field_validator("health_url")
    @classmethod
    def validate_health_url(cls, v: str) -> str:
        """
        Validates that health_url is either a valid HTTP/HTTPS address or
        a parseable host:port TCP socket string.
        """
        stripped = v.strip()
        if stripped.startswith(("http://", "https://")):
            return stripped
            
        parts = stripped.split(":")
        if len(parts) == 2:
            host, port_str = parts
            if host and port_str.isdigit():
                port_val = int(port_str)
                if 1 <= port_val <= 65535:
                    return stripped
                    
        raise ValueError(
            "Health URL must be a valid HTTP/HTTPS address (e.g. http://localhost:8001/health) "
            "or a host:port TCP address (e.g. localhost:5432)"
        )

class ServiceCreate(ServiceBase):
    """
    Input schema to register a new monitored service.
    """
    pass

class ServiceUpdate(BaseModel):
    """
    Input schema to modify an existing service target's settings.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    environment: Optional[str] = Field(None, pattern="^(Development|Testing|Production)$")
    health_url: Optional[str] = Field(None)
    response_time_threshold: Optional[int] = Field(None, ge=10, le=30000)
    cpu_threshold: Optional[float] = Field(None, ge=0.0, le=100.0)
    memory_threshold: Optional[float] = Field(None, ge=0.0, le=100.0)

    @field_validator("health_url")
    @classmethod
    def validate_health_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return ServiceBase.validate_health_url(v)

class ServiceResponse(ServiceBase):
    """
    Output schema representing a monitored service.
    """
    id: int
    ip_address: str
    port: int
    created_at: datetime
    updated_at: datetime

    # Rich SRE status fields dynamically calculated from latest health check history
    status: str = "Unknown"  # Healthy, Warning, Critical, Offline, Unknown
    response_time: float = 0.0
    availability: float = 100.0
    
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    
    version: Optional[str] = "Unknown"
    uptime_str: Optional[str] = "Unknown"
    hostname: Optional[str] = "Unknown"
    
    # Historical status arrays for rendering status grid and sparklines
    history_statuses: List[str] = []   # Last N health status strings
    history_latencies: List[float] = [] # Last N response time floats

    model_config = ConfigDict(from_attributes=True)
