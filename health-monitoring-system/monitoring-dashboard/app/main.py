"""
Central entrypoint bootstrap script for the SRE Monitoring Dashboard FastAPI application.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.logging import setup_logging, app_logger, error_logger
from app.services.monitoring_service import MonitoringService
from app.routers import auth, dashboard, services, health, logs

# Configure lifespan events to handle APScheduler threads startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Sequence
    setup_logging()
    app_logger.info("Main: Starting up SRE Infrastructure Health Monitoring Portal...")
    
    # Start APScheduler daemon thread
    MonitoringService.start_scheduler()
    
    yield
    
    # Shutdown Sequence
    app_logger.info("Main: Shutting down SRE Infrastructure Health Monitoring Portal...")
    MonitoringService.stop_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Production-grade DevOps Infrastructure Health Check Panel.",
    lifespan=lifespan
)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount SRE static assets
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(services.router)
app.include_router(logs.router)
app.include_router(health.router)

# Define templates loader to render custom error page views
templates = Jinja2Templates(directory="app/templates")

# ----------------------------------------------------
# Global Exception Handlers
# ----------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Differentiates exceptions between API fetches (JSON output) and direct browser page loads.
    """
    accept_header = request.headers.get("accept", "")
    is_html_request = "text/html" in accept_header
    
    # If HTML browser page, redirect or render login/unauthorized pages
    if is_html_request:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        # Fallback to base page with error details
        return HTMLResponse(
            content=f"<html><body><h2>Error {exc.status_code}</h2><p>{exc.detail}</p><a href='/'>Go back to Dashboard</a></body></html>",
            status_code=exc.status_code
        )
        
    # Else return consistent JSON response format
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catches all unhandled exceptions, logs detailed SRE trace, and returns HTTP 500.
    """
    error_logger.critical(f"Unhandled Exception: {str(exc)}", exc_info=True)
    
    accept_header = request.headers.get("accept", "")
    is_html_request = "text/html" in accept_header
    
    if is_html_request:
        return HTMLResponse(
            content="<html><body><h2>Internal Server Error (500)</h2><p>An unexpected database or application error occurred.</p></body></html>",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server database error or process timeout."}
    )
