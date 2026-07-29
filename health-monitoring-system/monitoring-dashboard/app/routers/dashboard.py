"""
Router defining dashboard HTML page rendering and stats API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import schemas
from app.dependencies import get_db, get_current_user_optional, get_current_user
from app.services.dashboard_service import DashboardService

logger = logging.getLogger("app")
router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def render_dashboard(
    request: Request, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Renders the central Grafana-like monitoring dashboard page view.
    Redirects to the authentication login portal if not logged in.
    """
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    summary = DashboardService.get_dashboard_summary(db)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html", 
        context={
            "app_name": "SRE Monitoring",
            "user": current_user,
            "summary": summary
        }
    )

@router.get(
    "/dashboard", 
    response_model=schemas.DashboardSummary,
    summary="Dashboard Summary JSON Metrics",
    description="Exposes compiled counts of healthy/offline nodes, system memory/disk usage, and alert timeline logs."
)
def get_dashboard_summary_api(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> schemas.DashboardSummary:
    """
    API endpoint returning dashboard card totals and alerts list.
    """
    logger.info(f"API Request: GET /dashboard - Requested by: {current_user.email}")
    return DashboardService.get_dashboard_summary(db)
