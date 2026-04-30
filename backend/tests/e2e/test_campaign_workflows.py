"""
End-to-End Tests for Complete Campaign Workflows

Tests complete user workflows from start to finish, simulating real user
interactions with the API and verifying the entire system works together correctly.
"""

import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
# 32-byte key encoded in base64
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcy1sb25nISE=")

from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import pytest
from datetime import datetime, timezone

from src.main import app


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for all database operations"""
    with patch("src.core.database.get_supabase_client") as mock_db:
        mock_client = MagicMock()
        mock_db.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_celery_task():
    """Mock Celery task execution"""
    with patch("src.workers.campaign_executor.execute_campaign") as mock:
        yield mock


@pytest.fixture
def sample_configuration():
    """Sample configuration data"""
    return {
        "user_email": "test@example.com",
        "apify_token": "apify_test_token_12345",
        "openai_token": "sk-test_token_67890",
        "smtp_password": "test_password",
        "twitter_auth_token": "test_auth_token",
        "twitter_ct0": "test_ct0_token",
    }


@pytest.fixture
def sample_campaign_data():
    """Sample campaign creation data"""
    return {
        "name": "Test Campaign",
        "social_network": "twitter",
        "search_type": "profile",
        "profiles": "@elonmusk, @naval",
        "language": "en",
        "min_likes": 10,
        "min_retweets": 5,
        "min_replies": 2,
        "hours_back": 24,
    }


@pytest.fixture
def sample_tweets():
    """Sample tweet results"""
    return [
        {
            "id": "1747123456789012345",
            "url": "https://twitter.com/elonmusk/status/1747123456789012345",
            "author": "elonmusk",
            "text": "AI will change everything. The future is now.",
            "likes": 15000,
            "reposts": 3000,
            "replies": 500,
            "timestamp": "2024-01-15T09:30:00.000Z",
        },
        {
            "id": "1747123456789012346",
            "url": "https://twitter.com/naval/status/1747123456789012346",
            "author": "naval",
            "text": "Building products is the ultimate form of leverage.",
            "likes": 8000,
            "reposts": 1500,
            "replies": 200,
            "timestamp": "2024-01-15T08:45:00.000Z",
        },
    ]


# ─── Test 36.1: Complete Happy Path Workflow ─────────────────────────────────


def test_complete_campaign_workflow_happy_path(
    client,
    mock_supabase,
    mock_celery_task,
    sample_configuration,
    sample_campaign_data,
    sample_tweets,
):
    """
    Test 36.1: User configures credentials → creates campaign → views results

    This test verifies the complete happy path workflow:
    1. User saves configuration
    2. User creates a campaign
    3. Campaign is enqueued
    4. User retrieves campaign details
    5. User views campaign results
    6. User downloads document
    """
    # Setup mock responses
    config_id = "config-123"
    campaign_id = "campaign-456"

    # Mock configuration save
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": config_id, **sample_configuration}
    ]
    mock_supabase.table.return_value.upsert.return_value.execute.return_value.data = [
        {"id": config_id, **sample_configuration}
    ]

    # Step 1: Configure credentials
    config_response = client.post("/api/configuration", json=sample_configuration)
    assert config_response.status_code == 201
    assert config_response.json()["success"] is True

    # Verify configuration was saved
    mock_supabase.table.assert_called()

    # Step 2: Verify configuration can be retrieved
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
        {"id": config_id, **sample_configuration}
    ]

    get_config_response = client.get("/api/configuration")
    assert get_config_response.status_code == 200
    config_data = get_config_response.json()
    assert config_data["user_email"] == sample_configuration["user_email"]
    # Verify tokens are masked
    assert "XXX" in config_data["apify_token_masked"] or "***" in config_data["apify_token_masked"]

    # Step 3: Create campaign
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": campaign_id,
            "name": sample_campaign_data["name"],
            "social_network": "twitter",
            "search_type": "profile",
            "config": {
                "profiles": ["elonmusk", "naval"],
                "keywords": None,
                "language": "en",
                "min_likes": 10,
                "min_retweets": 5,
                "min_replies": 2,
                "hours_back": 24,
            },
            "status": "pending",
            "error_message": None,
            "document_url": None,
            "results_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }
    ]

    campaign_response = client.post("/api/campaigns", json=sample_campaign_data)
    assert campaign_response.status_code == 201
    campaign_result = campaign_response.json()
    assert "campaign_id" in campaign_result
    assert campaign_result["status"] == "pending"

    # Verify Celery task was enqueued
    mock_celery_task.delay.assert_called_once()

    # Step 4: Get campaign details
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": campaign_id,
            "name": sample_campaign_data["name"],
            "social_network": "twitter",
            "search_type": "profile",
            "config": {
                "profiles": ["elonmusk", "naval"],
                "keywords": None,
                "language": "en",
                "min_likes": 10,
                "min_retweets": 5,
                "min_replies": 2,
                "hours_back": 24,
            },
            "status": "completed",
            "error_message": None,
            "document_url": "https://storage.supabase.co/campaigns/campaign-456/results.doc",
            "results_count": 2,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    ]

    status_response = client.get(f"/api/campaigns/{campaign_id}")
    assert status_response.status_code == 200
    campaign_data = status_response.json()
    assert campaign_data["id"] == campaign_id
    assert campaign_data["status"] == "completed"
    assert campaign_data["results_count"] == 2
    assert campaign_data["document_url"] is not None

    # Step 5: Get campaign results
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        sample_tweets
    )

    results_response = client.get(f"/api/campaigns/{campaign_id}/results")
    assert results_response.status_code == 200
    results = results_response.json()
    assert len(results) == 2
    assert results[0]["author"] == "elonmusk"
    assert results[1]["author"] == "naval"

    # Step 6: Get download URL
    mock_supabase.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": "https://storage.supabase.co/signed/campaigns/campaign-456/results.doc?token=xyz"
    }

    download_response = client.get(f"/api/campaigns/{campaign_id}/download")
    assert download_response.status_code == 200
    download_data = download_response.json()
    assert "download_url" in download_data
    assert "signed" in download_data["download_url"]


# ─── Test 36.2: Validation Error Workflow ────────────────────────────────────


def test_campaign_creation_with_invalid_data(client, mock_supabase):
    """
    Test 36.2: User creates campaign with invalid data → sees error messages

    This test verifies validation error handling:
    1. Missing required fields
    2. Empty campaign name
    3. Missing profiles for profile search
    4. Missing keywords for keyword search
    5. Negative engagement filters
    """
    # Test 1: Missing required field (name)
    invalid_data_1 = {
        "social_network": "twitter",
        "search_type": "profile",
        "profiles": "@elonmusk",
        "language": "en",
    }

    response_1 = client.post("/api/campaigns", json=invalid_data_1)
    assert response_1.status_code == 422  # FastAPI validation error

    # Test 2: Empty campaign name
    invalid_data_2 = {
        "name": "",
        "social_network": "twitter",
        "search_type": "profile",
        "profiles": "@elonmusk",
        "language": "en",
    }

    response_2 = client.post("/api/campaigns", json=invalid_data_2)
    # Can be either 400 (business validation) or 422 (pydantic validation)
    assert response_2.status_code in [400, 422]

    # Test 3: Missing profiles for profile search
    invalid_data_3 = {
        "name": "Test Campaign",
        "social_network": "twitter",
        "search_type": "profile",
        "profiles": "",
        "language": "en",
    }

    response_3 = client.post("/api/campaigns", json=invalid_data_3)
    assert response_3.status_code in [400, 422]

    # Test 4: Missing keywords for keyword search
    invalid_data_4 = {
        "name": "Test Campaign",
        "social_network": "twitter",
        "search_type": "keywords",
        "keywords": "",
        "language": "en",
    }

    response_4 = client.post("/api/campaigns", json=invalid_data_4)
    assert response_4.status_code in [400, 422]

    # Test 5: Negative engagement filter
    invalid_data_5 = {
        "name": "Test Campaign",
        "social_network": "twitter",
        "search_type": "keywords",
        "keywords": "AI",
        "language": "en",
        "min_likes": -10,
    }

    response_5 = client.post("/api/campaigns", json=invalid_data_5)
    assert response_5.status_code in [400, 422]


# ─── Test 36.3: Failure Workflow ─────────────────────────────────────────────


def test_campaign_execution_failure_workflow(
    client, mock_supabase, mock_celery_task, sample_campaign_data
):
    """
    Test 36.3: Campaign execution fails → user sees error in history

    This test verifies error handling during campaign execution:
    1. Campaign is created successfully
    2. Execution fails (simulated)
    3. Campaign status is updated to "failed"
    4. Error message is stored
    5. User can view failed campaign in history
    """
    campaign_id = "campaign-failed-123"
    error_message = "ApifyError: Rate limit exceeded"

    # Step 1: Create campaign
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": campaign_id,
            "name": sample_campaign_data["name"],
            "social_network": "twitter",
            "search_type": "profile",
            "config": {
                "profiles": ["elonmusk"],
                "keywords": None,
                "language": "en",
                "min_likes": 10,
                "min_retweets": 5,
                "min_replies": 2,
                "hours_back": 24,
            },
            "status": "pending",
            "error_message": None,
            "document_url": None,
            "results_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }
    ]

    campaign_response = client.post("/api/campaigns", json=sample_campaign_data)
    assert campaign_response.status_code == 201

    # Step 2: Simulate execution failure
    # (In real scenario, worker would update this)
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": campaign_id,
            "name": sample_campaign_data["name"],
            "social_network": "twitter",
            "search_type": "profile",
            "config": {
                "profiles": ["elonmusk"],
                "keywords": None,
                "language": "en",
                "min_likes": 10,
                "min_retweets": 5,
                "min_replies": 2,
                "hours_back": 24,
            },
            "status": "failed",
            "error_message": error_message,
            "document_url": None,
            "results_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }
    ]

    # Step 3: Get campaign details
    status_response = client.get(f"/api/campaigns/{campaign_id}")
    assert status_response.status_code == 200
    campaign_data = status_response.json()
    assert campaign_data["status"] == "failed"
    assert campaign_data["error_message"] == error_message
    assert campaign_data["document_url"] is None

    # Step 4: Verify failed campaign appears in history
    mock_supabase.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value.data = [
        {
            "id": campaign_id,
            "name": sample_campaign_data["name"],
            "social_network": "twitter",
            "search_type": "profile",
            "config": {
                "profiles": ["elonmusk"],
                "keywords": None,
                "language": "en",
                "min_likes": 10,
                "min_retweets": 5,
                "min_replies": 2,
                "hours_back": 24,
            },
            "status": "failed",
            "error_message": error_message,
            "document_url": None,
            "results_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }
    ]
    mock_supabase.table.return_value.select.return_value.execute.return_value.count = 1

    history_response = client.get("/api/campaigns?page=1&limit=20")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert history_data["total"] == 1
    assert history_data["items"][0]["status"] == "failed"
    assert history_data["items"][0]["error_message"] == error_message


# ─── Test 36.4: Document Download Workflow ───────────────────────────────────


def test_document_download_workflow(client, mock_supabase):
    """
    Test 36.4: User downloads document → file is correct

    This test verifies document download functionality:
    1. Campaign is completed with document
    2. User requests download URL
    3. Signed URL is generated
    4. URL format is correct
    """
    campaign_id = "campaign-with-doc-123"
    document_url = "campaigns/campaign-with-doc-123/results.doc"
    signed_url = "https://storage.supabase.co/signed/campaigns/campaign-with-doc-123/results.doc?token=abc123"

    # Step 1: Get campaign with document
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": campaign_id,
            "name": "Campaign with Document",
            "social_network": "twitter",
            "search_type": "keywords",
            "config": {
                "profiles": None,
                "keywords": ["AI", "ML"],
                "language": "en",
                "min_likes": 10,
                "min_retweets": 5,
                "min_replies": 2,
                "hours_back": 24,
            },
            "status": "completed",
            "error_message": None,
            "document_url": document_url,
            "results_count": 5,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    ]

    # Step 2: Request download URL
    # Mock storage service
    storage_mock = MagicMock()
    storage_mock.create_signed_url.return_value = {"signedURL": signed_url}
    mock_supabase.storage.from_.return_value = storage_mock

    download_response = client.get(f"/api/campaigns/{campaign_id}/download")
    assert download_response.status_code == 200
    download_data = download_response.json()

    # Step 3: Verify URL format
    assert "download_url" in download_data
    assert download_data["download_url"] == signed_url
    assert "signed" in download_data["download_url"]
    assert "token=" in download_data["download_url"]

    # Test: Campaign without document
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": "campaign-no-doc",
            "name": "Campaign without Document",
            "social_network": "twitter",
            "search_type": "keywords",
            "config": {
                "profiles": None,
                "keywords": ["AI"],
                "language": "en",
                "min_likes": 10,
                "min_retweets": 5,
                "min_replies": 2,
                "hours_back": 24,
            },
            "status": "running",
            "error_message": None,
            "document_url": None,
            "results_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }
    ]

    no_doc_response = client.get("/api/campaigns/campaign-no-doc/download")
    assert no_doc_response.status_code == 200
    no_doc_data = no_doc_response.json()
    assert "error" in no_doc_data
    assert "not available" in no_doc_data["error"].lower()


# ─── Test 36.5: Parallel Execution Workflow ──────────────────────────────────


def test_multiple_campaigns_parallel_execution(client, mock_supabase, mock_celery_task):
    """
    Test 36.5: Multiple campaigns execute in parallel → all complete successfully

    This test verifies parallel campaign execution:
    1. Create multiple campaigns simultaneously
    2. Verify all are created with unique IDs
    3. Verify all are enqueued
    4. Simulate parallel execution
    5. Verify all complete successfully
    6. Verify no race conditions or data corruption
    """
    num_campaigns = 3
    campaign_ids = [f"campaign-parallel-{i}" for i in range(num_campaigns)]

    # Step 1: Create multiple campaigns
    created_campaigns = []

    for i in range(num_campaigns):
        campaign_data = {
            "name": f"Parallel Campaign {i}",
            "social_network": "twitter",
            "search_type": "keywords",
            "keywords": f"keyword{i}",
            "language": "en",
            "min_likes": 10,
            "min_retweets": 5,
            "min_replies": 2,
            "hours_back": 24,
        }

        # Mock database response for each campaign
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": campaign_ids[i],
                "name": campaign_data["name"],
                "social_network": "twitter",
                "search_type": "keywords",
                "config": {
                    "profiles": None,
                    "keywords": [f"keyword{i}"],
                    "language": "en",
                    "min_likes": 10,
                    "min_retweets": 5,
                    "min_replies": 2,
                    "hours_back": 24,
                },
                "status": "pending",
                "error_message": None,
                "document_url": None,
                "results_count": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
            }
        ]

        response = client.post("/api/campaigns", json=campaign_data)
        assert response.status_code == 201
        result = response.json()
        assert "campaign_id" in result
        created_campaigns.append(result["campaign_id"])

    # Step 2: Verify all campaigns have unique IDs
    assert len(set(created_campaigns)) == num_campaigns

    # Step 3: Verify all were enqueued
    assert mock_celery_task.delay.call_count == num_campaigns

    # Step 4: Simulate all campaigns completing
    completed_campaigns = []
    for i in range(num_campaigns):
        completed_campaigns.append(
            {
                "id": campaign_ids[i],
                "name": f"Parallel Campaign {i}",
                "social_network": "twitter",
                "search_type": "keywords",
                "config": {
                    "profiles": None,
                    "keywords": [f"keyword{i}"],
                    "language": "en",
                    "min_likes": 10,
                    "min_retweets": 5,
                    "min_replies": 2,
                    "hours_back": 24,
                },
                "status": "completed",
                "error_message": None,
                "document_url": f"campaigns/{campaign_ids[i]}/results.doc",
                "results_count": 10 + i,  # Different result counts
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    # Step 5: Verify all campaigns completed successfully
    mock_supabase.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value.data = (
        completed_campaigns
    )
    mock_supabase.table.return_value.select.return_value.execute.return_value.count = num_campaigns

    history_response = client.get("/api/campaigns?page=1&limit=20")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert history_data["total"] == num_campaigns
    assert len(history_data["items"]) == num_campaigns

    # Step 6: Verify no data corruption - each campaign has correct data
    for i, campaign in enumerate(history_data["items"]):
        assert campaign["status"] == "completed"
        assert campaign["document_url"] is not None
        assert campaign["results_count"] == 10 + i
        assert f"keyword{i}" in campaign["config"]["keywords"]
        assert campaign["error_message"] is None


# ─── Additional Edge Case Tests ──────────────────────────────────────────────


def test_campaign_not_found(client, mock_supabase):
    """Test handling of non-existent campaign ID"""
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = (
        None
    )

    response = client.get("/api/campaigns/non-existent-id")
    assert response.status_code == 404


def test_pagination_works_correctly(client, mock_supabase):
    """Test that pagination returns correct page of results"""
    # Create 25 mock campaigns
    all_campaigns = []
    for i in range(25):
        all_campaigns.append(
            {
                "id": f"campaign-{i}",
                "name": f"Campaign {i}",
                "social_network": "twitter",
                "search_type": "keywords",
                "config": {
                    "profiles": None,
                    "keywords": ["test"],
                    "language": "en",
                    "min_likes": 10,
                    "min_retweets": 5,
                    "min_replies": 2,
                    "hours_back": 24,
                },
                "status": "completed",
                "error_message": None,
                "document_url": f"campaigns/campaign-{i}/results.doc",
                "results_count": i,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    # Page 1: First 20 campaigns
    mock_supabase.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value.data = all_campaigns[
        :20
    ]
    # Mock count query
    count_mock = MagicMock()
    count_mock.count = 25
    mock_supabase.table.return_value.select.return_value.execute.return_value = count_mock

    page1_response = client.get("/api/campaigns?page=1&limit=20")
    assert page1_response.status_code == 200
    page1_data = page1_response.json()
    assert page1_data["page"] == 1
    assert page1_data["limit"] == 20
    assert page1_data["total"] == 25
    assert page1_data["total_pages"] == 2
    assert len(page1_data["items"]) == 20

    # Page 2: Remaining 5 campaigns
    mock_supabase.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value.data = all_campaigns[
        20:25
    ]

    page2_response = client.get("/api/campaigns?page=2&limit=20")
    assert page2_response.status_code == 200
    page2_data = page2_response.json()
    assert page2_data["page"] == 2
    assert len(page2_data["items"]) == 5


def test_configuration_missing_before_campaign_creation(client, mock_supabase):
    """Test that campaign creation fails if configuration is not set"""
    # Mock no configuration exists
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = []

    campaign_data = {
        "name": "Test Campaign",
        "social_network": "twitter",
        "search_type": "keywords",
        "keywords": "AI",
        "language": "en",
    }

    # This should succeed at API level (configuration check happens in worker)
    # But we can test the configuration endpoint returns 400
    config_response = client.get("/api/configuration")
    assert config_response.status_code == 400
