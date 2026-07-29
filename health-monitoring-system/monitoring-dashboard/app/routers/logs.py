"""
Router defining REST API endpoints and views for Health check, Audit, and Application logs.
Supports pagination, sorting, search, and filtering.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import schemas
from app.database.models import Service
from app.dependencies import get_db, get_current_user_optional, get_current_user
from app.services.health_service import HealthService
from app.repositories.service import service_repo

logger = logging.getLogger("app")
router = APIRouter(tags=["Logs"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/logs/view", response_class=HTMLResponse)
def render_logs_page(
    request: Request,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Renders the log explorer dashboard viewport.
    """
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    services = service_repo.get_multi(db)
    return templates.TemplateResponse(
        request=request,
        name="service_logs.html",
        context={
            "app_name": "SRE Monitoring",
            "user": current_user,
            "services": services
        }
    )

@router.get("/logs")
def get_logs_api(
    type: str = Query("health", pattern="^(health|audit|application)$"),
    service_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """
    Retrieves logs of the selected type.
    - Type 'health': Query HealthLog table (supports pagination and filtering).
    - Type 'audit': Query AuditLog table (supports pagination).
    - Type 'application': Reads live Python process logs from 'logs/application.log'.
    """
    logger.info(f"API Request: GET /logs?type={type}&page={page}&limit={limit} - Requested by: {current_user.email}")
    
    # Calculate offset offset
    skip = (page - 1) * limit
    
    # 1. Health check logs
    if type == "health":
        logs = HealthService.query_health_logs(
            db, 
            service_id=service_id, 
            status=status, 
            skip=skip, 
            limit=limit
        )
        return [
            {
                "id": log.id,
                "service_id": log.service_id,
                "service_name": db.query(Service.name).filter(Service.id == log.service_id).scalar() or "Unknown",
                "timestamp": log.timestamp.isoformat() + "Z",
                "status": log.status,
                "response_time": log.response_time,
                "http_status": log.http_status,
                "remarks": log.remarks
            }
            for log in logs
        ]
        
    # 2. Operator Audit logs
    elif type == "audit":
        logs = HealthService.query_audit_logs(db, skip=skip, limit=limit)
        return [
            {
                "id": log.id,
                "user_email": db.query(schemas.user.User.email).filter(schemas.user.User.id == log.user_id).scalar() if log.user_id else "System",
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp.isoformat() + "Z"
            }
            for log in logs
        ]
        
    # 3. Live Application logging (logs/application.log)
    else:
        import os
        log_file = "logs/application.log"
        lines_list = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    # Read last 100 lines
                    lines = f.readlines()
                    lines_list = [line.strip() for line in lines[-100:]]
            except Exception as e:
                lines_list = [f"Error reading application log file: {str(e)}"]
        else:
            lines_list = ["Application log file 'logs/application.log' not generated yet."]
            
        return {"logs": lines_list}
