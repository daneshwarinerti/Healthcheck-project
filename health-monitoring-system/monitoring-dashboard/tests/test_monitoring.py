"""
Unit and integration tests validating APScheduler health checks and status logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status
from app.services.monitoring_service import probe_service, execute_health_checks
from app.database.models import Service, HealthLog

@pytest.mark.asyncio
async def test_probe_service_http_healthy():
    """
    Tests that a successful HTTP probe returns Healthy status and SRE metadata.
    """
    # Patch httpx.AsyncClient.get to mock microservice response
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Use MagicMock for synchronous response attributes to prevent coroutine warnings
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "service": "Mock User API",
            "status": "healthy",
            "version": "1.0.1",
            "uptime": "3d 4h",
            "hostname": "user-api-host-01"
        }
        mock_get.return_value = mock_response
        
        res = await probe_service(
            service_id=1,
            name="Mock User API",
            health_url="http://localhost:8001/health",
            threshold_ms=1000
        )
        
        svc_id, status_val, latency, http_status, remarks, version, uptime, hostname = res
        
        assert svc_id == 1
        assert status_val == "Healthy"
        assert http_status == 200
        assert version == "1.0.1"
        assert uptime == "3d 4h"
        assert hostname == "user-api-host-01"
        assert "err=" not in remarks if remarks else True

@pytest.mark.asyncio
async def test_probe_service_http_latency_warning():
    """
    Tests status changes to Warning when latency exceeds 500ms (but is below threshold limit).
    """
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        # Mock time.perf_counter to simulate 600ms latency delay
        with patch("time.perf_counter", side_effect=[0.0, 0.6]):
            res = await probe_service(
                service_id=2,
                name="Slow Service",
                health_url="http://localhost:8002/health",
                threshold_ms=1000
            )
            
            status_val = res[1]
            assert status_val == "Warning"

@pytest.mark.asyncio
async def test_probe_service_http_offline_timeout():
    """
    Tests that offline/timeout network requests return Offline status.
    """
    import httpx
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectTimeout("Connection timed out")):
        res = await probe_service(
            service_id=3,
            name="Timed Out Service",
            health_url="http://localhost:8003/health",
            threshold_ms=1000
        )
        
        status_val = res[1]
        assert status_val == "Offline"
        assert "ConnectTimeout" in res[4]
