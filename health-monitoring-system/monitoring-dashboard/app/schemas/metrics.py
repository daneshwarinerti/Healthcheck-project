"""
Pydantic schemas for psutil system metrics and dashboard summaries.
"""

from typing import Dict, List, Any
from pydantic import BaseModel

class SystemMetricsResponse(BaseModel):
    """
    Schema for real system telemetry metrics parsed via psutil.
    """
    cpu_percent: float
    cpu_cores: int
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    system_uptime: str
    hostname: str
    platform: str
    python_version: str

class AlertTimelineItem(BaseModel):
    """
    Schema representing a single entry on the dashboard alerts timeline.
    """
    timestamp: str
    service_name: str
    message: str
    type: str  # danger, warning, success, secondary

class DashboardSummary(BaseModel):
    """
    Unified summary schema for top metrics cards and charts.
    """
    # Service counts
    total_services: int
    healthy_services: int
    warning_services: int
    critical_services: int
    offline_services: int
    unknown_services: int
    
    # Latency aggregates
    avg_response_time: float  # ms
    
    # System metrics snapshot
    system: SystemMetricsResponse
    
    # Alert history panel feed
    alerts: List[AlertTimelineItem]
