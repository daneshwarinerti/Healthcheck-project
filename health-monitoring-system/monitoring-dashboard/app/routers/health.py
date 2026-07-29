"""
Router defining REST API endpoints for liveness probes and psutil telemetry.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import schemas
from app.dependencies import get_db, get_current_user
from app.services.health_service import HealthService
from app.repositories.service import service_repo

logger = logging.getLogger("app")
router = APIRouter(tags=["Health & Telemetry"])

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Core System Health",
    description="Liveness probe to check database connectivity responsiveness."
)
def system_health_probe(db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Checks database connection health.
    """
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as ex:
        logger.error(f"Liveness health probe failure: {str(ex)}")
        return {"status": "unhealthy", "database": "disconnected"}

@router.get(
    "/metrics/system",
    response_model=schemas.SystemMetricsResponse,
    summary="Get Hardware System Metrics",
    description="Exposes live CPU, memory, disk, network, and hostname metadata collected using psutil."
)
def get_system_metrics_api(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns live system metrics.
    """
    return HealthService.get_system_metrics()

@router.get(
    "/metrics/services",
    summary="Get Monitored Services Metrics List",
    description="Returns SRE status details of all monitored nodes."
)
def get_services_metrics_api(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Returns list of monitored target nodes.
    """
    services = service_repo.get_multi(db)
    metrics_list = []
    for s in services:
        rich_svc = service_repo.get_service_response(db, s)
        metrics_list.append({
            "service_id": rich_svc.id,
            "name": rich_svc.name,
            "environment": rich_svc.environment,
            "health_url": rich_svc.health_url,
            "status": rich_svc.status,
            "response_time_ms": rich_svc.response_time,
            "availability_percent": rich_svc.availability,
            "version": rich_svc.version,
            "hostname": rich_svc.hostname
        })
    return metrics_list
