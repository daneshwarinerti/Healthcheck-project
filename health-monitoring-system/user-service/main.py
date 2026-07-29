import time
import socket
import psutil
from datetime import datetime
from fastapi import FastAPI, Request

app = FastAPI(title="User Service", version="1.0.0")

# Record server boot parameters
boot_time = time.time()
hostname = socket.gethostname()
request_counter = 0

@app.middleware("http")
async def log_request_counter(request: Request, call_next):
    """
    HTTP middleware tracking request rates across endpoints.
    """
    global request_counter
    # Exclude health probe checks from metrics counting to avoid inflation
    if not request.url.path.endswith(("/health", "/metrics")):
        request_counter += 1
    response = await call_next(request)
    return response

def get_uptime_string() -> str:
    """
    Dynamically computes the server uptime.
    """
    uptime_seconds = int(time.time() - boot_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)

@app.get("/")
def read_root():
    """
    Welcome API Portal documentation index.
    """
    return {
        "service": "User Service",
        "status": "online",
        "endpoints": ["/", "/health", "/info", "/version", "/metrics", "/users"]
    }

@app.get("/health")
def health():
    """
    Exposes SRE-compliant health check metadata (including host CPU/RAM states).
    """
    cpu_usage = psutil.cpu_percent(interval=None)
    mem_usage = psutil.virtual_memory().percent
    
    return {
        "service": "User Service",
        "status": "healthy",
        "version": "1.0.0",
        "hostname": hostname,
        "uptime": get_uptime_string(),
        "cpu": cpu_usage,
        "memory": mem_usage,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/info")
def info():
    """
    Exposes generic service information description.
    """
    return {
        "service": "User Service",
        "description": "User profile management and identity validation API microservice.",
        "environment": "production",
        "hostname": hostname
    }

@app.get("/version")
def version():
    """
    Exposes service version metadata.
    """
    return {
        "service": "User Service",
        "version": "1.0.0"
    }

@app.get("/metrics")
def metrics():
    """
    Exposes telemetry request rates and uptime metrics.
    """
    return {
        "service": "User Service",
        "total_requests": request_counter,
        "uptime_seconds": int(time.time() - boot_time)
    }

@app.get("/users")
def get_users():
    """
    Returns a sample list of users.
    """
    return [
        {"id": 1, "username": "sre_operator", "email": "operator@example.com"},
        {"id": 2, "username": "devops_admin", "email": "admin@example.com"},
        {"id": 3, "username": "viewer_user", "email": "viewer@example.com"}
    ]
