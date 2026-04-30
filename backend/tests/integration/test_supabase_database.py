"""
Integration Tests for Supabase Database Operations

Tests CRUD operations for campaigns, configurations, results, and analysis.
Uses realistic mocked Supabase client responses.
"""

import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from uuid import uuid4
import pytest

from src.repositories.campaign_repository import CampaignRepository
from src.repositories.configuration_repository import ConfigurationRepository


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    return Mock()


@pytest.fixture
def campaign_repository(mock_supabase_client):
    """Campaign repository with mocked client"""
    return CampaignRepository(mock_supabase_client)


@pytest.fixture
def configuration_repository(mock_supabase_client):
    """Configuration repository with mocked client"""
    return ConfigurationRepository(mock_supabase_client)


@pytest.fixture
def realistic_campaign_data():
    """Realistic campaign database record"""
    return {
        "id": str(uuid4()),
        "name": "AI Trends Campaign",
        "social_network": "twitter",
        "search_type": "keywords",
        "status": "pending",
        "config": {
            "profiles": [],
            "keywords": ["AI", "machine learning"],
            "language": "en",
            "min_likes": 100,
            "min_retweets": 50,
            "min_replies": 10,
            "hours_back": 24,
        },
        "results_count": 0,
        "document_url": None,
        "error_message": None,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        "completed_at": None,
    }


@pytest.fixture
def realistic_configuration_data():
    """Realistic configuration database record"""
    return {
        "id": str(uuid4()),
        "user_email": "user@example.com",
        "apify_token": "encrypted_apify_token_base64",
        "openai_token": "encrypted_openai_token_base64",
        "smtp_password": "encrypted_smtp_password_base64",
        "twitter_auth_token": "encrypted_twitter_auth_base64",
        "twitter_ct0": "encrypted_twitter_ct0_base64",
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }


@pytest.fixture
def realistic_tweet_results():
    """Realistic tweet results for database"""
    return [
        {
            "id": "1747123456789012345",
            "url": "https://twitter.com/elonmusk/status/1747123456789012345",
            "author": "elonmusk",
            "text": "AI will change everything",
            "likes": 15000,
            "reposts": 3000,
            "replies": 500,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        },
        {
            "id": "1747123456789012346",
            "url": "https://twitter.com/naval/status/1747123456789012346",
            "author": "naval",
            "text": "Building products is leverage",
            "likes": 8000,
            "reposts": 1500,
            "replies": 200,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        },
    ]


# ─── Test Campaign CRUD Operations ───────────────────────────────────────────


def test_create_campaign(campaign_repository, mock_supabase_client, realistic_campaign_data):
    """Test creating a new campaign"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = [realistic_campaign_data]
    mock_table.insert.return_value.execute.return_value = mock_response

    result = campaign_repository.create(realistic_campaign_data)

    # Verify table was accessed correctly
    mock_supabase_client.table.assert_called_once_with("campaigns")
    mock_table.insert.assert_called_once_with(realistic_campaign_data)

    # Verify result
    assert result["id"] == realistic_campaign_data["id"]
    assert result["name"] == "AI Trends Campaign"
    assert result["status"] == "pending"


def test_get_campaign_by_id(campaign_repository, mock_supabase_client, realistic_campaign_data):
    """Test retrieving a campaign by ID"""
    campaign_id = realistic_campaign_data["id"]

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = [realistic_campaign_data]
    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    result = campaign_repository.get_by_id(campaign_id)

    # Verify query chain
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.eq.assert_called_once_with("id", campaign_id)

    # Verify result
    assert result is not None
    assert result["id"] == campaign_id


def test_get_campaign_by_id_not_found(campaign_repository, mock_supabase_client):
    """Test retrieving non-existent campaign returns None"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = []  # Empty result
    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    result = campaign_repository.get_by_id("nonexistent-id")

    assert result is None


def test_list_campaigns_with_pagination(
    campaign_repository, mock_supabase_client, realistic_campaign_data
):
    """Test listing campaigns with pagination"""
    campaigns = [realistic_campaign_data.copy() for _ in range(5)]

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = campaigns
    mock_table.select.return_value.order.return_value.range.return_value.execute.return_value = (
        mock_response
    )

    result = campaign_repository.list_all(limit=5, offset=0)

    # Verify query chain
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.order.assert_called_once_with("created_at", desc=True)
    mock_table.select.return_value.order.return_value.range.assert_called_once_with(0, 4)

    # Verify result
    assert len(result) == 5


def test_count_campaigns(campaign_repository, mock_supabase_client):
    """Test counting total campaigns"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.count = 42
    mock_table.select.return_value.execute.return_value = mock_response

    count = campaign_repository.count_all()

    # Verify query
    mock_table.select.assert_called_once_with("id", count="exact")

    # Verify result
    assert count == 42


def test_update_campaign_status_to_running(campaign_repository, mock_supabase_client):
    """Test updating campaign status to running"""
    campaign_id = str(uuid4())

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    campaign_repository.update_status(campaign_id, "running")

    # Verify update was called
    mock_table.update.assert_called_once()
    update_data = mock_table.update.call_args[0][0]
    assert update_data["status"] == "running"

    # Verify query chain
    mock_table.update.return_value.eq.assert_called_once_with("id", campaign_id)


def test_update_campaign_status_to_completed(campaign_repository, mock_supabase_client):
    """Test updating campaign status to completed with results"""
    campaign_id = str(uuid4())
    document_url = "https://storage.example.com/doc.docx"

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    campaign_repository.update_status(
        campaign_id, "completed", document_url=document_url, results_count=50
    )

    # Verify update data
    update_data = mock_table.update.call_args[0][0]
    assert update_data["status"] == "completed"
    assert update_data["document_url"] == document_url
    assert update_data["results_count"] == 50
    assert "completed_at" in update_data


def test_update_campaign_status_to_failed(campaign_repository, mock_supabase_client):
    """Test updating campaign status to failed with error message"""
    campaign_id = str(uuid4())
    error_msg = "API rate limit exceeded"

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    campaign_repository.update_status(campaign_id, "failed", error_message=error_msg)

    # Verify update data
    update_data = mock_table.update.call_args[0][0]
    assert update_data["status"] == "failed"
    assert update_data["error_message"] == error_msg


# ─── Test Campaign Results Operations ────────────────────────────────────────


def test_save_campaign_results(campaign_repository, mock_supabase_client, realistic_tweet_results):
    """Test saving tweet results for a campaign"""
    campaign_id = str(uuid4())

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    campaign_repository.save_results(campaign_id, realistic_tweet_results)

    # Verify correct table was accessed
    mock_supabase_client.table.assert_called_once_with("campaign_results")

    # Verify insert was called with campaign_id added to each record
    insert_call = mock_table.insert.call_args[0][0]
    assert len(insert_call) == 2
    assert all(r["campaign_id"] == campaign_id for r in insert_call)


def test_save_empty_results(campaign_repository, mock_supabase_client):
    """Test saving empty results does nothing"""
    campaign_id = str(uuid4())

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    campaign_repository.save_results(campaign_id, [])

    # Should not call insert for empty list
    mock_table.insert.assert_not_called()


def test_get_campaign_results(campaign_repository, mock_supabase_client, realistic_tweet_results):
    """Test retrieving campaign results"""
    campaign_id = str(uuid4())

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = realistic_tweet_results
    mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_response
    )

    results = campaign_repository.get_results(campaign_id)

    # Verify query chain
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.eq.assert_called_once_with("campaign_id", campaign_id)
    mock_table.select.return_value.eq.return_value.order.assert_called_once_with(
        "timestamp", desc=True
    )

    # Verify results
    assert len(results) == 2
    assert results[0]["author"] == "elonmusk"


# ─── Test Campaign Analysis Operations ───────────────────────────────────────


def test_save_campaign_analysis(campaign_repository, mock_supabase_client):
    """Test saving analysis for a campaign"""
    campaign_id = str(uuid4())
    analysis_text = '{"summary": "Test analysis", "key_themes": ["AI"]}'

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    campaign_repository.save_analysis(campaign_id, analysis_text)

    # Verify correct table was accessed
    mock_supabase_client.table.assert_called_once_with("campaign_analysis")

    # Verify insert data
    insert_data = mock_table.insert.call_args[0][0]
    assert insert_data["campaign_id"] == campaign_id
    assert insert_data["analysis_text"] == analysis_text


def test_get_campaign_analysis(campaign_repository, mock_supabase_client):
    """Test retrieving campaign analysis"""
    campaign_id = str(uuid4())
    analysis_data = {
        "id": str(uuid4()),
        "campaign_id": campaign_id,
        "analysis_text": '{"summary": "Test", "key_themes": []}',
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = [analysis_data]
    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    result = campaign_repository.get_analysis(campaign_id)

    # Verify query chain
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.eq.assert_called_once_with("campaign_id", campaign_id)

    # Verify result
    assert result is not None
    assert result["campaign_id"] == campaign_id


def test_get_campaign_analysis_not_found(campaign_repository, mock_supabase_client):
    """Test retrieving non-existent analysis returns None"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = []
    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    result = campaign_repository.get_analysis("nonexistent-id")

    assert result is None


# ─── Test Configuration CRUD Operations ──────────────────────────────────────


def test_create_configuration(
    configuration_repository, mock_supabase_client, realistic_configuration_data
):
    """Test creating a new configuration"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = [realistic_configuration_data]
    mock_table.insert.return_value.execute.return_value = mock_response

    result = configuration_repository.create(realistic_configuration_data)

    # Verify table was accessed correctly
    mock_supabase_client.table.assert_called_once_with("configurations")
    mock_table.insert.assert_called_once_with(realistic_configuration_data)

    # Verify result
    assert result["user_email"] == "user@example.com"


def test_get_configuration(
    configuration_repository, mock_supabase_client, realistic_configuration_data
):
    """Test retrieving configuration"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = [realistic_configuration_data]
    mock_table.select.return_value.limit.return_value.execute.return_value = mock_response

    result = configuration_repository.get()

    # Verify query
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.limit.assert_called_once_with(1)

    # Verify result
    assert result is not None
    assert result["user_email"] == "user@example.com"


def test_get_configuration_not_found(configuration_repository, mock_supabase_client):
    """Test retrieving non-existent configuration returns None"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = []
    mock_table.select.return_value.limit.return_value.execute.return_value = mock_response

    result = configuration_repository.get()

    assert result is None


def test_get_configuration_by_email(
    configuration_repository, mock_supabase_client, realistic_configuration_data
):
    """Test retrieving configuration by email"""
    email = "user@example.com"

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = [realistic_configuration_data]
    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    result = configuration_repository.get_by_email(email)

    # Verify query chain
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.eq.assert_called_once_with("user_email", email)

    # Verify result
    assert result is not None
    assert result["user_email"] == email


def test_update_configuration(configuration_repository, mock_supabase_client):
    """Test updating configuration"""
    config_id = str(uuid4())
    updates = {"apify_token": "new_encrypted_token", "openai_token": "new_encrypted_openai_token"}

    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = [{"id": config_id, **updates}]
    mock_table.update.return_value.eq.return_value.execute.return_value = mock_response

    result = configuration_repository.update(config_id, updates)

    # Verify update was called
    mock_table.update.assert_called_once_with(updates)
    mock_table.update.return_value.eq.assert_called_once_with("id", config_id)

    # Verify result
    assert result["id"] == config_id


def test_configuration_exists(configuration_repository, mock_supabase_client):
    """Test checking if configuration exists"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = [{"id": str(uuid4())}]
    mock_table.select.return_value.limit.return_value.execute.return_value = mock_response

    exists = configuration_repository.exists()

    # Verify query
    mock_table.select.assert_called_once_with("id")

    # Verify result
    assert exists is True


def test_configuration_not_exists(configuration_repository, mock_supabase_client):
    """Test checking if configuration exists when it doesn't"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table

    mock_response = Mock()
    mock_response.data = []
    mock_table.select.return_value.limit.return_value.execute.return_value = mock_response

    exists = configuration_repository.exists()

    assert exists is False


# ─── Test Error Handling ─────────────────────────────────────────────────────


def test_database_connection_error(campaign_repository, mock_supabase_client):
    """Test handling of database connection errors"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table
    mock_table.select.side_effect = Exception("Connection failed")

    with pytest.raises(Exception) as exc_info:
        campaign_repository.get_by_id("test-id")

    assert "Connection failed" in str(exc_info.value)


def test_transaction_rollback_on_error(campaign_repository, mock_supabase_client):
    """Test that errors during operations are properly raised"""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table
    mock_table.insert.return_value.execute.side_effect = Exception("Insert failed")

    with pytest.raises(Exception) as exc_info:
        campaign_repository.create({"name": "Test"})

    assert "Insert failed" in str(exc_info.value)
