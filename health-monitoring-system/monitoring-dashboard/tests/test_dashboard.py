"""
Integration tests validating SRE dashboard summaries and telemetry metrics.
"""

import pytest
from fastapi import status
from app.database.models import Service, HealthLog
from tests.test_services import get_auth_token

def test_dashboard_unauthorized(client):
    """
    Tests that requesting the dashboard summary without a token returns HTTP 401.
    """
    res = client.get("/dashboard")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_dashboard_summary_and_metrics_success(client, db):
    """
    Tests successful retrieval of dashboard summaries and hardware metrics under authentication.
    """
    # 1. Authenticate SRE Operator
    token = get_auth_token(client, "dashboard_operator@example.com", "Operator")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Register mock service in DB to avoid empty states
    mock_svc = Service(
        name="Telemetry Node",
        environment="Production",
        health_url="http://localhost:8001/health",
        ip_address="127.0.0.1",
        port=8001,
        response_time_threshold=1000
    )
    db.add(mock_svc)
    db.commit()
    
    # Add healthy log for this service
    mock_log = HealthLog(
        service_id=mock_svc.id,
        status="Healthy",
        response_time=120.0,
        http_status=200,
        remarks="v=1.0.0|up=1d|host=localhost-01"
    )
    db.add(mock_log)
    db.commit()
    
    # 3. Retrieve Dashboard Summary
    res = client.get("/dashboard", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_services"] == 1
    assert data["healthy_services"] == 1
    assert data["avg_response_time"] == 120.0
    
    # Verify hardware metrics format
    sys_metrics = data["system"]
    assert "cpu_percent" in sys_metrics
    assert "memory_percent" in sys_metrics
    assert "disk_percent" in sys_metrics
    assert "network_sent_mb" in sys_metrics

def test_metrics_endpoints(client):
    """
    Tests system and service specific endpoints directly.
    """
    token = get_auth_token(client, "metrics_admin@example.com", "Admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. System Metrics
    res_sys = client.get("/metrics/system", headers=headers)
    assert res_sys.status_code == status.HTTP_200_OK
    assert "cpu_cores" in res_sys.json()
    
    # 2. Services Metrics
    res_svc = client.get("/metrics/services", headers=headers)
    assert res_svc.status_code == status.HTTP_200_OK
    assert isinstance(res_svc.json(), list)
