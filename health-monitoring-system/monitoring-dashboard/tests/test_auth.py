"""
Integration tests validating user authentication, complexity rules, and login endpoints.
"""

import pytest
from fastapi import status

def test_user_registration_success(client):
    """
    Tests successful account registration matching SRE complexity rules.
    """
    payload = {
        "first_name": "SRE",
        "last_name": "Engineer",
        "email": "sre@example.com",
        "password": "StrongPassword@123",
        "confirm_password": "StrongPassword@123",
        "role": "Operator"
    }
    res = client.post("/register", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["email"] == "sre@example.com"
    assert data["role"] == "Operator"
    assert "id" in data

def test_user_registration_password_mismatch(client):
    """
    Tests that registration fails when confirmation password does not match.
    """
    payload = {
        "first_name": "SRE",
        "last_name": "Engineer",
        "email": "sre@example.com",
        "password": "StrongPassword@123",
        "confirm_password": "DifferentPassword@123",
        "role": "Operator"
    }
    res = client.post("/register", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = res.json()
    # Check pydantic validation details
    assert "Passwords do not match" in str(data["detail"])

def test_user_registration_password_too_weak(client):
    """
    Tests that registration fails when password lacks complexity requirements (no uppercase, no special chars, etc.).
    """
    # Lacks numbers and special characters
    payload = {
        "first_name": "SRE",
        "last_name": "Engineer",
        "email": "sre@example.com",
        "password": "weak",
        "confirm_password": "weak",
        "role": "Operator"
    }
    res = client.post("/register", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = res.json()
    assert "String should have at least 8 characters" in str(data["detail"])

def test_user_registration_duplicate_email(client):
    """
    Tests that duplicate emails are rejected.
    """
    payload = {
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@example.com",
        "password": "AdminPassword@123",
        "confirm_password": "AdminPassword@123",
        "role": "Admin"
    }
    # Create first
    res = client.post("/register", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    
    # Try duplicate
    res_dup = client.post("/register", json=payload)
    assert res_dup.status_code == status.HTTP_400_BAD_REQUEST
    assert "email address already exists" in res_dup.json()["detail"]

def test_user_login_success(client):
    """
    Tests successful login authentication yielding valid access token.
    """
    # 1. Register user
    reg_payload = {
        "first_name": "SRE",
        "last_name": "Engineer",
        "email": "login@example.com",
        "password": "StrongPassword@123",
        "confirm_password": "StrongPassword@123",
        "role": "Operator"
    }
    client.post("/register", json=reg_payload)
    
    # 2. Login
    login_payload = {
        "email": "login@example.com",
        "password": "StrongPassword@123"
    }
    res = client.post("/login", json=login_payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "Operator"

def test_user_login_failure(client):
    """
    Tests login rejection on incorrect credentials.
    """
    login_payload = {
        "email": "unknown@example.com",
        "password": "WrongPassword@123"
    }
    res = client.post("/login", json=login_payload)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in res.json()["detail"]
