# Health Check Dashboard

A production-ready, interview-grade **Health Check Dashboard** built with a clean, decoupled architecture using **FastAPI** (Python) on the backend and a premium **Bootstrap 5 / Vanilla JavaScript** theme on the frontend. 

The application is structured using a service-based architecture to isolate business logic, enforce strict input validations (server name formatting and IP syntax), and implement robust global exception handling.

---

## Folder Structure

The project conforms to the following clean architecture format:

```text
health-dashboard/
├── app/
│   ├── main.py              # Application startup, middleware, and exception handlers
│   ├── database.py          # Session manager and SQLAlchemy engine
│   ├── models.py            # User and Server database ORM models
│   ├── schemas.py           # Pydantic models (validation, serialization, documentation examples)
│   ├── auth.py              # CryptContext security configuration and JWT token validators
│   ├── services/            # SERVICE LAYER (Isolates business logic from routing)
│   │   ├── auth.py          # Verification services and session audits
│   │   └── servers.py       # CRUD operations, summaries, and simulation update metrics
│   ├── routers/             # ROUTING LAYER (HTTP endpoints mapping and Swagger parameters)
│   │   ├── auth.py          # Endpoint: /api/auth
│   │   ├── servers.py       # Endpoint: /api/servers
│   │   └── health.py        # Endpoints: /health, /dashboard, /metrics
│   ├── templates/           # VIEW TEMPLATES
│   │   ├── login.html       # Centered, glassmorphic login viewport
│   │   └── dashboard.html   # Live monitored status metrics board
│   └── static/              # STATIC ASSETS
│       ├── css/
│       │   └── style.css    # Typography, dark/light theme, and animation parameters
│       └── js/
│           └── dashboard.js # Data loaders, toast notifications, and modals
├── requirements.txt         # Project package requirements
└── README.md                # System documentation
```

---

## Local Setup

### Prerequisites
- Python 3.12+
- SQLite (default for development) or PostgreSQL (for production)

### Setup Steps
1. **Navigate into the folder**:
   ```bash
   cd health-dashboard
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Start local development server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *Note: Upon startup, the database is automatically created (via SQLite `health.db`) and pre-seeded with 5 default monitored servers and an administrator account (`username: admin`, `password: admin`).*

6. **Verify URL accessibility**:
   - Web Dashboard: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - Swagger API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Prometheus telemetry scraping endpoint: [http://127.0.0.1:8000/metrics](http://127.0.0.1:8000/metrics)

---

## Environment Variables

Configure application settings by exporting these environment variables:

| Variable Name  | Type   | Default Value                    | Description                                                           |
|----------------|--------|----------------------------------|-----------------------------------------------------------------------|
| `APP_NAME`     | String | `Health Check Dashboard`         | Display title of the application dashboard.                           |
| `DATABASE_URL` | String | `sqlite:///./health.db`          | Connection URL for database (supports SQLite and PostgreSQL).          |
| `SECRET_KEY`   | String | `super-secret-key-development`   | Cryptographic signature key for encoding JWT authentication tokens.  |
| `PORT`         | Int    | `8000`                           | Running port configuration.                                           |

---

## API Documentation

FastAPI automatically generates comprehensive Swagger-compliant documentation containing interactive schema definitions and example payloads.

### Authentication
- `POST /api/auth/login`: Authenticates administrator user credentials and returns a JWT access token.

### Servers (CRUD)
- `GET /api/servers`: Retrieves all configured servers.
- `GET /api/servers/{id}`: Retrieves a single server by its database ID.
- `POST /api/servers`: Registers a new server (Requires JWT token).
- `PUT /api/servers/{id}`: Updates a server configuration (Requires JWT token).
- `DELETE /api/servers/{id}`: Removes a server from monitoring configurations (Requires JWT token).

### Monitoring & Telemetry
- `GET /health`: Standard liveness and database connection check.
- `GET /dashboard`: Aggregated statistics (total counts, healthy counts, CPU and memory averages).
- `GET /metrics`: Returns metrics formatted for Prometheus scrapers (`health_server_status`, `health_server_cpu_usage`, `health_server_memory_usage`, etc.).

---

## Screenshots Section
*(Add screenshots demonstrating the dashboard status grid, dark/light theme switchers, server CRUD modal forms, and token verification errors).*

- **Main Dashboard (Dark Mode)**: Showcases live system cards, status tags, and usage bars.
- **Form Validation error notifications**: Displays real-time feedback when entering invalid IPs or duplicate server names.
- **Admin authentication**: Displays modal configurations visible only to authenticated users.

---

## Future Improvements
- **Live WebSocket Synchronisation**: Shift from 10-second polling to full real-time push-notifications.
- **Historical Metrics Persistence**: Introduce a timeseries database to chart historical CPU/Memory averages instead of displaying instantaneous values.
- **Notification Webhooks**: Integrate Slack or Email dispatch services to notify personnel instantly when a server enters `Critical` or `Offline` states.
