import time
import socket
import psutil
from datetime import datetime
from fastapi import FastAPI, Request

app = FastAPI(title="Notification Service", version="1.1.2")

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
        "service": "Notification Service",
        "status": "online",
        "endpoints": ["/", "/health", "/info", "/version", "/metrics", "/notifications"]
    }

@app.get("/health")
def health():
    """
    Exposes SRE-compliant health check metadata (including host CPU/RAM states).
    """
    cpu_usage = psutil.cpu_percent(interval=None)
    mem_usage = psutil.virtual_memory().percent
    
    return {
        "service": "Notification Service",
        "status": "healthy",
        "version": "1.1.2",
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
        "service": "Notification Service",
        "description": "E-mail dispatches, Slack notifications and SMS broadcast API.",
        "environment": "production",
        "hostname": hostname
    }

@app.get("/version")
def version():
    """
    Exposes service version metadata.
    """
    return {
        "service": "Notification Service",
        "version": "1.1.2"
    }

@app.get("/metrics")
def metrics():
    """
    Exposes telemetry request rates and uptime metrics.
    """
    return {
        "service": "Notification Service",
        "total_requests": request_counter,
        "uptime_seconds": int(time.time() - boot_time)
    }

@app.get("/notifications")
def get_notifications():
    """
    Returns a sample list of dispatch audits.
    """
    return [
        {"id": 1, "channel": "email", "recipient": "admin@example.com", "status": "sent"},
        {"id": 2, "channel": "slack", "recipient": "#alerts", "status": "delivered"},
        {"id": 3, "channel": "sms", "recipient": "+15550199", "status": "failed"}
    ]
