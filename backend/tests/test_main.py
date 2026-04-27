"""Tests for main application"""


def test_root_endpoint(client):
    """Test root endpoint returns correct response"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "message" in data
    assert "version" in data
    assert "docs" in data


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


def test_api_health_endpoint(client):
    """Test API health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "api_version" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]
    assert "celery" in data["services"]


def test_cors_headers(client):
    """Test CORS headers are present"""
    # Test with actual GET request since OPTIONS may not be implemented for all routes
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # CORS middleware should add these headers
    assert "access-control-allow-origin" in response.headers or "Access-Control-Allow-Origin" in response.headers


def test_process_time_header(client):
    """Test that X-Process-Time header is added to responses"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Process-Time" in response.headers
    # Verify it's a valid float
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0
