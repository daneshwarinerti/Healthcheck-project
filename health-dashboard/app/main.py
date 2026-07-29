"""
Main entrypoint for the FastAPI Health Check Dashboard application.

This module initializes the application, registers routers, handles global exceptions,
manages database tables seeding, and runs the background thread for metrics simulation.
"""

import os
import sys
import time
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import auth, models, database
from app.database import SessionLocal, engine
from app.routers import auth as auth_router, health as health_router, servers as servers_router
from app.services.servers import ServerService

# Setup logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("app")

APP_NAME: str = os.getenv("APP_NAME", "Health Check Dashboard")
running: bool = True

def seed_database(db: Session) -> None:
    """
    Seeds the database with default administrator credentials and
    initial target servers for monitoring visualization.
    """
    # 1. Create Default Admin User
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        logger.info("Main: Seeding default admin user...")
        hashed = auth.get_password_hash("admin")
        db.add(models.User(username="admin", hashed_password=hashed))
        db.commit()
        logger.info("Main: Default admin credentials seeded (Username: 'admin', Password: 'admin')")
        
    # 2. Seed Initial Servers
    servers_count = db.query(models.Server).count()
    if servers_count == 0:
        logger.info("Main: Seeding initial monitored servers...")
        initial_targets = [
            {"name": "API-01", "environment": "Prod", "ip_address": "10.0.0.10", "uptime": 15},
            {"name": "DB-01", "environment": "Prod", "ip_address": "10.0.0.20", "uptime": 22},
            {"name": "Redis-Cache", "environment": "Test", "ip_address": "10.0.1.15", "uptime": 8},
            {"name": "Auth-Service", "environment": "Dev", "ip_address": "10.0.2.5", "uptime": 3},
            {"name": "Backend-Worker", "environment": "Dev", "ip_address": "10.0.2.10", "uptime": 1}
        ]
        for t in initial_targets:
            # Seed starting healthy metrics
            cpu = float(random_randint := 10 + (t["uptime"] % 4) * 10)
            mem = float(random_randint + 5)
            server = models.Server(
                name=t["name"],
                environment=t["environment"],
                ip_address=t["ip_address"],
                cpu_usage=cpu,
                memory_usage=mem,
                status="Healthy",
                uptime=t["uptime"],
                last_checked=datetime.utcnow()
            )
            db.add(server)
        db.commit()
        logger.info("Main: Successfully seeded 5 initial monitored servers.")

async def simulate_metrics_loop() -> None:
    """
    Asynchronous loop that triggers server metrics updating every 10 seconds.
    """
    logger.info("Main: Starting background simulation loop...")
    while running:
        await asyncio.sleep(10)
        db: Session = SessionLocal()
        try:
            ServerService.update_simulated_metrics(db)
            logger.info("Main: Server simulation updated successfully")
        except Exception as ex:
            logger.error(f"Main: Exception in simulation updater: {str(ex)}", exc_info=True)
            db.rollback()
        finally:
            db.close()

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown hooks.
    """
    logger.info(f"Main: Starting up '{APP_NAME}'...")
    
    # Create DB tables
    models.Base.metadata.create_all(bind=engine)
    
    # Seeding database
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
        
    # Start the simulation background task
    task = asyncio.create_task(simulate_metrics_loop())
    
    yield
    
    # Shutdown hook
    logger.info("Main: Shutting down application...")
    global running
    running = False
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Main: Simulation background task stopped")

# Initialize FastAPI App
app = FastAPI(
    title=APP_NAME,
    description="Production-ready FastAPI backend for server health check monitoring.",
    version="1.1.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request duration log middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        f"API Request: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration_ms:.2f}ms"
    )
    return response

# ----------------------------------------------------
# Global Exception Handlers
# ----------------------------------------------------

@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Catches all database-related connection and transaction errors.
    """
    logger.error(f"Global DB Error: {str(exc)} on request {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database connection or transaction failure. Please try again later."}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Catches Pydantic schema validation errors and returns a formatted JSON.
    """
    logger.warning(f"Global Validation Error: {str(exc.errors())} on request {request.url.path}")
    
    # Build readable custom message list
    error_details = []
    for err in exc.errors():
        loc = " -> ".join(str(loc) for loc in err["loc"])
        msg = err["msg"]
        error_details.append(f"{loc}: {msg}")
        
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Input validation error", "errors": error_details}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches all uncaught system exceptions.
    """
    logger.error(f"Global Unhandled Exception: {str(exc)} on request {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please contact the administrator."}
    )

# Static and Templates mounting
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Register Routers
app.include_router(auth_router.router)
app.include_router(servers_router.router)
app.include_router(health_router.router)

# Page Routes for HTML templates
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"app_name": APP_NAME})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"app_name": APP_NAME})
