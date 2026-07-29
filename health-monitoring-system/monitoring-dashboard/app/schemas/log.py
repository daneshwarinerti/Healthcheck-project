"""
Pydantic schemas for Health check logs and Audit logs.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class HealthLogResponse(BaseModel):
    """
    Output schema for service health probe records.
    """
    id: int
    service_id: int
    timestamp: datetime
    status: str  # Healthy, Warning, Critical, Offline, Unknown
    response_time: float
    http_status: Optional[int] = None
    remarks: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    """
    Output schema for SRE operator action records.
    """
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None  # Custom field to output user context easily
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
