"""Pytest configuration and fixtures"""

import os
import pytest
from fastapi.testclient import TestClient


# Set test environment variables before importing app
@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_KEY"] = "test-key"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/1"
    os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/1"
    os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-bytes-long!!"
    os.environ["DEBUG"] = "True"


@pytest.fixture
def client():
    """FastAPI test client"""
    from src.main import app

    return TestClient(app)


@pytest.fixture
def sample_configuration():
    """Sample configuration data for testing"""
    return {
        "user_email": "test@example.com",
        "apify_token": "apify_test_token_12345",
        "openai_token": "sk-test_token_67890",
        "smtp_password": "test_password",
    }


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing"""
    return {
        "name": "Test Campaign",
        "social_network": "twitter",
        "search_type": "profile",
        "profiles": "@elonmusk, @naval",
        "language": "en",
        "min_likes": 10,
        "min_retweets": 5,
        "min_replies": 2,
    }
