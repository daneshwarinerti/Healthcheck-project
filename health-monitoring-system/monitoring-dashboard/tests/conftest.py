"""
Pytest configuration file defining fixtures for database sessions and test client overrides.
"""

import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Force testing environment config loading
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///./test_health.db"

# Append project root to sys.path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database.session import Base
from app.dependencies import get_db
from fastapi.testclient import TestClient

# SQLite test database file path
TEST_DB_FILE = "./test_health.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Session-scoped fixture to create and tear down the database schema tables.
    """
    # Clean up any leftover file
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass
            
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    
    # Final cleanup
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

@pytest.fixture
def db() -> sessionmaker:
    """
    Function-scoped fixture creating a clean database session context.
    Wraps execution inside a transaction that is rolled back after each test completes.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db) -> TestClient:
    """
    Function-scoped fixture overriding the FastAPI DB dependency with our test session.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    # Apply override mapping
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_c:
        yield test_c
    # Clear overrides to avoid pollution
    app.dependency_overrides.clear()
