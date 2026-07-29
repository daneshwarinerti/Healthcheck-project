"""
Router defining service configurations, HTML views, and management REST APIs.
"""

import logging
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import schemas
from app.database.models import Service, HealthLog
from app.repositories.service import service_repo
from app.repositories.log import audit_log_repo, health_log_repo
from app.dependencies import get_db, get_current_user, get_current_user_optional, require_admin, require_operator
from app.services.monitoring_service import probe_service

logger = logging.getLogger("app")
router = APIRouter(tags=["Services"])
templates = Jinja2Templates(directory="app/templates")

# ----------------------------------------------------
# Page Rendering Routes (HTML)
# ----------------------------------------------------

@router.get("/services/new", response_class=HTMLResponse)
def render_create_service(
    request: Request,
    current_user = Depends(require_admin)
):
    """
    Renders the service creation form. Admin only.
    """
    return templates.TemplateResponse(
        "service_form.html",
        {
            "request": request,
            "app_name": "SRE Monitoring",
            "user": current_user,
            "service": None
        }
    )

@router.get("/services/{service_id}/edit", response_class=HTMLResponse)
def render_edit_service(
    service_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Renders the service modification form. Admin only.
    """
    service = service_repo.get(db, id=service_id)
    if not service:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    return templates.TemplateResponse(
        "service_form.html",
        {
            "request": request,
            "app_name": "SRE Monitoring",
            "user": current_user,
            "service": service
        }
    )

@router.get("/services/{service_id}", response_class=HTMLResponse)
def render_service_detail(
    service_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Renders the detailed SRE dashboard view for a specific service target,
    displaying description, availability calculations, timelines, and recent check logs.
    """
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    service = service_repo.get(db, id=service_id)
    if not service:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    rich_service = service_repo.get_service_response(db, service)
    return templates.TemplateResponse(
        "service_logs.html",
        {
            "request": request,
            "app_name": "SRE Monitoring",
            "user": current_user,
            "service": rich_service
        }
    )

# ----------------------------------------------------
# REST API Endpoints (JSON)
# ----------------------------------------------------

@router.get("/api/services", response_model=List[schemas.ServiceResponse])
def get_services_api(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    environment: Optional[str] = None,
    sort_by: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> List[schemas.ServiceResponse]:
    """
    Retrieves configured services populated with live state aggregates.
    Supports filtering by environment, text searching, pagination, and sorting.
    """
    services = service_repo.get_multi_filtered(
        db, 
        skip=skip, 
        limit=limit, 
        search=search, 
        environment=environment, 
        sort_by=sort_by
    )
    return [service_repo.get_service_response(db, s) for s in services]

@router.get("/api/services/{service_id}", response_model=schemas.ServiceResponse)
def get_service_api(
    service_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> schemas.ServiceResponse:
    """
    Retrieves detailed configuration and history stats for a specific service.
    """
    service = service_repo.get(db, id=service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID {service_id} not found."
        )
    return service_repo.get_service_response(db, service)

@router.post("/api/services", response_model=schemas.ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service_api(
    service_in: schemas.ServiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Creates a new monitored service configuration. Admin only.
    """
    # Name conflict verification
    existing = service_repo.get_by_name(db, service_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service with name '{service_in.name}' already exists."
        )
        
    # Split IP and Port from Health URL
    # Set default values, then try parsing
    ip_address = "127.0.0.1"
    port = 80
    
    url = service_in.health_url.strip()
    if url.startswith(("http://", "https://")):
        try:
            # Parse url host & port
            from urllib.parse import urlparse
            parsed = urlparse(url)
            ip_address = parsed.hostname or "127.0.0.1"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except Exception:
            pass
    else:
        try:
            parts = url.split(":")
            ip_address = parts[0]
            port = int(parts[1])
        except Exception:
            pass
            
    obj_in_data = {
        "name": service_in.name,
        "description": service_in.description,
        "environment": service_in.environment,
        "health_url": service_in.health_url,
        "ip_address": ip_address,
        "port": port,
        "response_time_threshold": service_in.response_time_threshold,
        "cpu_threshold": service_in.cpu_threshold,
        "memory_threshold": service_in.memory_threshold
    }
    
    new_svc = service_repo.create(db, obj_in_data=obj_in_data)
    
    # Audit log entry
    audit_log_repo.log_action(
        db,
        user_id=current_user.id,
        action="Service Created",
        details=f"Service '{new_svc.name}' configured targeting: {new_svc.health_url}",
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    
    # Trigger immediate initial probe check in background if event loop is running
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(probe_service(new_svc.id, new_svc.name, new_svc.health_url, new_svc.response_time_threshold))
    except RuntimeError:
        pass
    
    return service_repo.get_service_response(db, new_svc)

@router.put("/api/services/{service_id}", response_model=schemas.ServiceResponse)
def update_service_api(
    service_id: int,
    service_in: schemas.ServiceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Modifies a monitored service configuration. Admin only.
    """
    service = service_repo.get(db, id=service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service configuration not found."
        )
        
    if service_in.name is not None:
        existing = db.query(Service).filter(
            Service.name == service_in.name,
            Service.id != service_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Service with name '{service_in.name}' already exists."
            )
            
    # Compile updates
    obj_in_data = service_in.model_dump(exclude_unset=True)
    
    # Recalculate IP and Port if URL changes
    if "health_url" in obj_in_data and obj_in_data["health_url"]:
        url = obj_in_data["health_url"].strip()
        ip_address = "127.0.0.1"
        port = 80
        if url.startswith(("http://", "https://")):
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                ip_address = parsed.hostname or "127.0.0.1"
                port = parsed.port or (443 if parsed.scheme == "https" else 80)
            except Exception:
                pass
        else:
            try:
                parts = url.split(":")
                ip_address = parts[0]
                port = int(parts[1])
            except Exception:
                pass
        obj_in_data["ip_address"] = ip_address
        obj_in_data["port"] = port
        
    updated_svc = service_repo.update(db, db_obj=service, obj_in_data=obj_in_data)
    
    # Audit log entry
    audit_log_repo.log_action(
        db,
        user_id=current_user.id,
        action="Service Updated",
        details=f"Service '{updated_svc.name}' configuration parameters adjusted.",
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    
    return service_repo.get_service_response(db, updated_svc)

@router.delete("/api/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_api(
    service_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Deletes a service configuration. Admin only.
    """
    service = service_repo.get(db, id=service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service configuration not found."
        )
        
    service_name = service.name
    service_repo.remove(db, id=service_id)
    
    # Audit log entry
    audit_log_repo.log_action(
        db,
        user_id=current_user.id,
        action="Service Deleted",
        details=f"Service '{service_name}' removed from monitoring dashboard.",
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/api/services/{service_id}/check", response_model=schemas.ServiceResponse)
async def trigger_manual_check(
    service_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_operator)
):
    """
    Triggers an immediate, manual SRE health probe check. Operator or Admin only.
    """
    service = service_repo.get(db, id=service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found."
        )
        
    # Execute check synchronously inside API call for immediate UI update
    res_tuple = await probe_service(service.id, service.name, service.health_url, service.response_time_threshold)
    
    # Save log
    svc_id, status_val, latency, http_status, remarks, version, uptime, hostname = res_tuple
    
    # Combine SRE properties to store in remarks
    remarks_packed = f"v={version or '1.0.0'}|up={uptime or 'N/A'}|host={hostname or 'N/A'}"
    if remarks:
        remarks_packed += f"|err={remarks}"
        
    new_log = HealthLog(
        service_id=service.id,
        status=status_val,
        response_time=latency,
        http_status=http_status,
        remarks=remarks_packed,
        timestamp=datetime.utcnow()
    )
    db.add(new_log)
    
    # Audit log entry
    audit_log_repo.log_action(
        db,
        user_id=current_user.id,
        action="Manual Check Triggered",
        details=f"Manual check executed on service '{service.name}'. Outcome: {status_val}.",
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    db.commit()
    return service_repo.get_service_response(db, service)

@router.post("/api/services/{service_id}/ack")
def acknowledge_alert(
    service_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_operator)
):
    """
    Acknowledges active warning or critical alerts on a service. Operator or Admin only.
    """
    service = service_repo.get(db, id=service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found."
        )
        
    # Record acknowledgment in SRE Audit log
    details_text = f"Alert for service '{service.name}' acknowledged by operator: {current_user.email}."
    audit_log_repo.log_action(
        db,
        user_id=current_user.id,
        action="Alert Acknowledged",
        details=details_text,
        ip_address=request.client.host if request.client else "127.0.0.1"
    )
    return {"message": f"Alert for service '{service.name}' acknowledged successfully."}
