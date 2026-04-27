"""Tests for middleware components"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel


class TestItem(BaseModel):
    """Test model for validation"""

    name: str
    value: int


def test_http_exception_handling(client):
    """Test HTTP exception handler returns proper format"""
    # Test 404 endpoint
    response = client.get("/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "code" in data
    assert "message" in data
    assert "path" in data
    assert data["code"] == 404


def test_validation_error_handling():
    """Test validation error handler returns proper format"""
    # Create a test app with validation
    app = FastAPI()

    @app.post("/test")
    async def test_endpoint(item: TestItem):
        return item

    client = TestClient(app)

    # Send invalid data
    response = client.post("/test", json={"name": "test"})  # Missing 'value'
    assert response.status_code == 422  # FastAPI default validation error
    data = response.json()
    assert "detail" in data


def test_request_logging_middleware(client):
    """Test request logging middleware adds process time header"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Process-Time" in response.headers
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0
    assert process_time < 10  # Should be very fast


def test_cors_middleware(client):
    """Test CORS middleware is configured"""
    response = client.options(
        "/health", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"}
    )
    assert response.status_code == 200
