"""
Router defining monitoring, health probes, dashboard metrics, and Prometheus scrape endpoints.
"""

import logging
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services.servers import ServerService

logger = logging.getLogger("app")
router = APIRouter(tags=["Monitoring"])

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check Probes",
    description="Tests server readiness and connectivity to the configured database layer."
)
def health_check(db: Session = Depends(get_db)) -> dict:
    """
    Checks database connection health.
    """
    logger.info("GET /health - Liveness/Readiness probe trigger")
    try:
        # Verify db responsiveness
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed database check: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": "Database connection is offline"
        }

@router.get(
    "/dashboard",
    response_model=schemas.DashboardSummary,
    status_code=status.HTTP_200_OK,
    summary="Dashboard Summary Stats",
    description="Compiles live aggregated statistics of all monitored target servers."
)
def get_dashboard_summary(db: Session = Depends(get_db)) -> schemas.DashboardSummary:
    """
    Get aggregated dashboard cards statistics.
    """
    logger.info("GET /dashboard - Compiling dashboard card aggregations")
    return ServerService.get_dashboard_summary(db)

@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Prometheus Telemetry Scraper",
    description="Exposes live system statuses in a Prometheus-compatible format."
)
def get_prometheus_metrics(db: Session = Depends(get_db)) -> Response:
    """
    Exposes metrics for Prometheus scraping.
    """
    logger.info("GET /metrics - Prometheus scraping invocation")
    servers = ServerService.get_all_servers(db)
    
    total = len(servers)
    healthy = sum(1 for s in servers if s.status == "Healthy")
    unhealthy = total - healthy
    
    lines = []
    
    # 1. Total configured servers
    lines.append("# HELP health_dashboard_total_servers Total number of servers configured.")
    lines.append("# TYPE health_dashboard_total_servers gauge")
    lines.append(f"health_dashboard_total_servers {total}")
    
    # 2. Healthy servers count
    lines.append("# HELP health_dashboard_healthy_servers Total number of healthy servers.")
    lines.append("# TYPE health_dashboard_healthy_servers gauge")
    lines.append(f"health_dashboard_healthy_servers {healthy}")
    
    # 3. Unhealthy servers count
    lines.append("# HELP health_dashboard_unhealthy_servers Total number of unhealthy servers.")
    lines.append("# TYPE health_dashboard_unhealthy_servers gauge")
    lines.append(f"health_dashboard_unhealthy_servers {unhealthy}")
    
    # 4. Individual Server Status (1 = Healthy, 0 = Offline/Warning/Critical)
    lines.append("# HELP health_server_status Individual server status (1 for Healthy, 0 for Warning/Critical/Offline).")
    lines.append("# TYPE health_server_status gauge")
    for s in servers:
        status_val = 1 if s.status == "Healthy" else 0
        lines.append(f'health_server_status{{name="{s.name}",env="{s.environment}",ip="{s.ip_address}"}} {status_val}')
        
    # 5. Individual Server CPU
    lines.append("# HELP health_server_cpu_usage Individual server CPU usage percentage.")
    lines.append("# TYPE health_server_cpu_usage gauge")
    for s in servers:
        lines.append(f'health_server_cpu_usage{{name="{s.name}",env="{s.environment}"}} {s.cpu_usage}')
        
    # 6. Individual Server Memory
    lines.append("# HELP health_server_memory_usage Individual server memory usage percentage.")
    lines.append("# TYPE health_server_memory_usage gauge")
    for s in servers:
        lines.append(f'health_server_memory_usage{{name="{s.name}",env="{s.environment}"}} {s.memory_usage}')
        
    # 7. Individual Server Uptime
    lines.append("# HELP health_server_uptime_days Individual server uptime in days.")
    lines.append("# TYPE health_server_uptime_days gauge")
    for s in servers:
        lines.append(f'health_server_uptime_days{{name="{s.name}",env="{s.environment}"}} {s.uptime}')
        
    content = "\n".join(lines) + "\n"
    return Response(content=content, media_type="text/plain; version=0.0.4")
