# SRE Infrastructure Health Monitoring System

This project is a production-grade mini system designed to monitor application target nodes. It comprises a central **Monitoring Dashboard** and three independent running microservices (**User Service**, **Payment Service**, and **Notification Service**).

```text
                     Browser (UI Portal)
                       │
                       ▼
          Health Monitoring Dashboard (Port 8000)
                       │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
  User Service     Payment Service   Notification Service
   (Port 8001)      (Port 8002)       (Port 8003)
       │                │                │
    /health          /health          /health
       │                │                │
       └────────────────┼────────────────┘
                        │
                PostgreSQL / SQLite
```

---

## Architecture & Technical Features

1. **Clean Architecture Patterns**: Built using FastAPI, SQLAlchemy, Repository Patterns, Services Layer, Pydantic v2 schemas, and discrete API Routers.
2. **Double-Layer Authentication Security**: Validates JWT access tokens from both HTTP Headers (REST API queries) and Secure HTTP-Only Cookies (browser page requests).
3. **SRE Operator RBAC Roles**:
   - `Admin`: Full control over target node configs (CRUD operations, registration).
   - `Operator`: Can trigger manual check sweeps and acknowledge active alerts.
   - `Viewer`: Read-only telemetry views.
4. **Grafana-Style Dark UI**: Glassmorphic styling, real-time Chart.js graphs, 100-check timeline grids, incident lists, and system resource monitors.
5. **Background Telemetry Scheduler**: Uses APScheduler executing parallel HTTP GET probes and TCP socket validation streams (Postgre, Redis, RabbitMQ) every 15 seconds.
6. **Separated Operational Logs**: Operations are separated into dedicated log files under `logs/`:
   - `logs/application.log`: Application runtime events.
   - `logs/health.log`: Automated target probe check outputs.
   - `logs/audit.log`: Administrative operator actions.
   - `logs/scheduler.log`: APScheduler daemon threads trace.
7. **Multi-Environment configuration Loader**: Selects variables dynamically based on `APP_ENV` (loads `.env.development`, `.env.testing`, or `.env.production`).

---

## Microservices API Specification

Each of the three services (`User`, `Payment`, `Notification`) exposes the following SRE endpoints:
- `GET /`: API entry point listing active coordinates.
- `GET /health`: Returns CPU/memory utilization, dynamic uptime calculations, server hostname, and timestamp.
- `GET /info`: Describes environmental settings.
- `GET /version`: Exposes current software deployment version.
- `GET /metrics`: Yields live request counts and uptime duration.

---

## Installation & Setup

### 1. Install Dependencies
Run the install command from the root directory to set up all required libraries:
```bash
pip install -r requirements.txt
```

### 2. Configure Database & Seed Data
Navigate to the dashboard directory, run database migrations, and seed default configs:
```bash
cd health-monitoring-system/monitoring-dashboard

# Create database tables schema
alembic upgrade head

# Seed initial operator users and targets
python app/seed.py
```

### 3. Run Applications
Start the microservices and the dashboard in separate terminal prompts:

* **Start User Service (Port 8001)**:
  ```bash
  cd health-monitoring-system/user-service
  uvicorn main:app --reload --port 8001
  ```

* **Start Payment Service (Port 8002)**:
  ```bash
  cd health-monitoring-system/payment-service
  uvicorn main:app --reload --port 8002
  ```

* **Start Notification Service (Port 8003)**:
  ```bash
  cd health-monitoring-system/notification-service
  uvicorn main:app --reload --port 8003
  ```

* **Start SRE Monitoring Dashboard (Port 8000)**:
  ```bash
  cd health-monitoring-system/monitoring-dashboard
  uvicorn app.main:app --reload --port 8000
  ```

---

## Running Unit & Integration Tests

We maintain a comprehensive pytest suite verifying security tokens, validations, database transactions, and network timeout states.

Run tests using the following command inside `monitoring-dashboard/`:
```bash
pytest
```

---

## Configuration & Environment Variables

Select the environment by setting the `APP_ENV` variable in your terminal session:
```powershell
# PowerShell
$env:APP_ENV="production"
# Command Prompt
set APP_ENV=production
```
- **Development** (`.env.development`): Configured with `health_dev.db`.
- **Testing** (`.env.testing`): Configured with `test_health.db` (auto-cleaned after test runs).
- **Production** (`.env.production`): Configured with production SQL databases.

---

## Authentication Credentials

* **System Administrator**:
  - Email: `admin@example.com`
  - Password: `Admin@123`
  
* **SRE Operator**:
  - Email: `operator@example.com`
  - Password: `Operator@123`

---

## Future DevOps Operations Roadmap

1. **Containerization**: Define separate `Dockerfiles` for each service and compile image targets.
2. **Local Orchestration**: Write a `docker-compose.yml` defining services, networking overlays, Postgres DB configurations, and volume directories.
3. **Cloud Kubernetes Deployments**: Scaffold Kubernetes YAML manifests (Deployments, Services, ConfigMaps, Secrets, Ingress controllers) for cloud orchestration.
4. **Helm Package Manager**: Package YAML templates into Helm Charts for versioned, parameter-driven deployments.
5. **CI/CD Integration**: Construct automated GitHub Actions pipelines to run pytests, compile Docker images, and push tag releases to registry hubs.
6. **Prometheus & Grafana**: Export standardized metrics targets (`/metrics`) to Prometheus servers and display telemetry charts on Grafana dashboards.
