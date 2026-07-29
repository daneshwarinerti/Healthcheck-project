"""
Integration tests validating service registration CRUD, URL parsing, and Operator triggers.
"""

import pytest
from fastapi import status
from app.database.models import Service

def get_auth_token(client, email: str, role: str) -> str:
    """
    Helper to quickly register, authenticate, and return a token for a specific role.
    """
    client.post("/register", json={
        "first_name": "SRE",
        "last_name": "Engineer",
        "email": email,
        "password": "StrongPassword@123",
        "confirm_password": "StrongPassword@123",
        "role": role
    })
    res = client.post("/login", json={
        "email": email,
        "password": "StrongPassword@123"
    })
    return res.json()["access_token"]

def test_service_crud_admin_permissions(client):
    """
    Tests that an Admin operator can perform full CRUD lifecycle adjustments.
    """
    token = get_auth_token(client, "admin_crud@example.com", "Admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Service
    payload = {
        "name": "Audit API Service",
        "description": "Exposes audit ledger metadata",
        "environment": "Production",
        "health_url": "http://localhost:8080/health",
        "response_time_threshold": 800,
        "cpu_threshold": 90.0,
        "memory_threshold": 90.0
    }
    res = client.post("/api/services", json=payload, headers=headers)
    assert res.status_code == status.HTTP_201_CREATED
    service_id = res.json()["id"]
    assert res.json()["name"] == "Audit API Service"
    assert res.json()["ip_address"] == "localhost"
    assert res.json()["port"] == 8080
    
    # 2. Update Service
    update_payload = {
        "description": "Updated SRE API",
        "response_time_threshold": 1200
    }
    res_update = client.put(f"/api/services/{service_id}", json=update_payload, headers=headers)
    assert res_update.status_code == status.HTTP_200_OK
    assert res_update.json()["description"] == "Updated SRE API"
    assert res_update.json()["response_time_threshold"] == 1200
    
    # 3. Delete Service
    res_delete = client.delete(f"/api/services/{service_id}", headers=headers)
    assert res_delete.status_code == status.HTTP_204_NO_CONTENT

def test_service_creation_invalid_role(client):
    """
    Tests that a Viewer or Operator cannot write/modify service node configurations.
    """
    viewer_token = get_auth_token(client, "viewer_test@example.com", "Viewer")
    headers = {"Authorization": f"Bearer {viewer_token}"}
    
    payload = {
        "name": "Audit Service Node",
        "environment": "Production",
        "health_url": "http://localhost:8080/health"
    }
    res = client.post("/api/services", json=payload, headers=headers)
    # Viewers are forbidden (403) from modifications
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_service_duplicate_rejection(client):
    """
    Tests that registering a service with an already registered name fails.
    """
    token = get_auth_token(client, "admin_dup@example.com", "Admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "name": "Unique Service",
        "environment": "Production",
        "health_url": "http://localhost:8080/health"
    }
    
    # First save succeeds
    client.post("/api/services", json=payload, headers=headers)
    
    # Duplicate save fails
    res = client.post("/api/services", json=payload, headers=headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in res.json()["detail"]

def test_service_url_validation(client):
    """
    Tests URL format validation rules (requires HTTP schemes or host:port socket format).
    """
    token = get_auth_token(client, "admin_val@example.com", "Admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Invalid URL scheme
    payload = {
        "name": "Invalid Node Service",
        "environment": "Production",
        "health_url": "ftp://localhost:8080"
    }
    res = client.post("/api/services", json=payload, headers=headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
