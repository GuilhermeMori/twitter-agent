"""
Integration Tests for Celery Task Execution

Tests complete campaign execution workflow with mocked external services.
Verifies task orchestration, retry logic, and error handling.
"""

import os
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
import pytest

# Skip all tests if Celery is not installed
pytest.importorskip("celery", reason="Celery not installed")

from src.workers.campaign_executor import execute_campaign, _is_transient_error


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def campaign_id():
    """Sample campaign ID"""
    return str(uuid4())


@pytest.fixture
def realistic_campaign_record():
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
            "hours_back": 24
        },
        "results_count": 0,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "updated_at": datetime.now(tz=timezone.utc).isoformat()
    }


@pytest.fixture
def realistic_configuration():
    """Realistic decrypted configuration"""
    return Mock(
        apify_token="apify_test_token_12345",
        openai_token="sk-test_openai_token_67890",
        smtp_password="test_smtp_password",
        user_email="user@example.com",
        twitter_auth_token="test_twitter_auth",
        twitter_ct0="test_ct0"
    )


@pytest.fixture
def realistic_tweets():
    """Realistic scraped tweets"""
    from src.models.campaign import Tweet
    
    return [
        Tweet(
            id="1747123456789012345",
            url="https://twitter.com/elonmusk/status/1747123456789012345",
            author="elonmusk",
            text="AI will change everything",
            likes=15000,
            reposts=3000,
            replies=500,
            timestamp=datetime.now(tz=timezone.utc)
        ),
        Tweet(
            id="1747123456789012346",
            url="https://twitter.com/naval/status/1747123456789012346",
            author="naval",
            text="Building products is leverage",
            likes=8000,
            reposts=1500,
            replies=200,
            timestamp=datetime.now(tz=timezone.utc)
        )
    ]


@pytest.fixture
def realistic_analysis():
    """Realistic analysis result"""
    from src.models.analysis import Analysis
    
    return Analysis(
        summary="The analyzed tweets focus on AI and product development.",
        key_themes=["AI", "Product Development", "Innovation"],
        sentiment="positive",
        top_influencers=["@elonmusk", "@naval"],
        recommendations=["Focus on AI content", "Engage with influencers"]
    )


# ─── Test Complete Campaign Execution Workflow ───────────────────────────────


@patch('src.workers.campaign_executor.StorageService')
@patch('src.workers.campaign_executor.EmailService')
@patch('src.workers.campaign_executor.DocumentGenerator')
@patch('src.workers.campaign_executor.AnalysisEngine')
@patch('src.workers.campaign_executor.ScrapingEngineFactory')
@patch('src.workers.campaign_executor.ConfigurationManager')
@patch('src.workers.campaign_executor.CampaignRepository')
@patch('src.workers.campaign_executor.get_supabase_client')
def test_complete_campaign_execution_success(
    mock_get_db,
    mock_campaign_repo_class,
    mock_config_mgr_class,
    mock_scraping_factory,
    mock_analysis_engine_class,
    mock_doc_gen_class,
    mock_email_service_class,
    mock_storage_service_class,
    campaign_id,
    realistic_campaign_record,
    realistic_configuration,
    realistic_tweets,
    realistic_analysis
):
    """Test complete successful campaign execution workflow"""
    # Mock database client
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    # Mock campaign repository
    mock_repo = Mock()
    mock_campaign_repo_class.return_value = mock_repo
    mock_repo.get_by_id.return_value = realistic_campaign_record
    
    # Mock configuration manager
    mock_config_mgr = Mock()
    mock_config_mgr_class.return_value = mock_config_mgr
    mock_config_mgr.get_configuration.return_value = realistic_configuration
    
    # Mock scraping engine
    mock_scraping_engine = Mock()
    mock_scraping_factory.create.return_value = mock_scraping_engine
    mock_scraping_engine.scrape.return_value = realistic_tweets
    
    # Mock analysis engine
    mock_analysis_engine = Mock()
    mock_analysis_engine_class.return_value = mock_analysis_engine
    mock_analysis_engine.analyze.return_value = realistic_analysis
    
    # Mock document generator
    mock_doc_gen = Mock()
    mock_doc_gen_class.return_value = mock_doc_gen
    mock_doc_gen.generate.return_value = "/tmp/campaign_results.docx"
    
    # Mock email service
    mock_email_service = Mock()
    mock_email_service_class.return_value = mock_email_service
    
    # Mock storage service
    mock_storage_service = Mock()
    mock_storage_service_class.return_value = mock_storage_service
    mock_storage_service.upload_document.return_value = "https://storage.example.com/doc.docx"
    
    # Execute campaign
    with patch('os.remove'):  # Mock file cleanup
        execute_campaign(campaign_id)
    
    # Verify workflow steps
    # 1. Status updated to running
    assert mock_repo.update_status.call_args_list[0][0][1] == "running"
    
    # 2. Configuration retrieved
    mock_config_mgr.get_configuration.assert_called_once()
    
    # 3. Scraping executed
    mock_scraping_engine.scrape.assert_called_once()
    
    # 4. Results saved
    mock_repo.save_results.assert_called_once()
    assert len(mock_repo.save_results.call_args[0][1]) == 2  # 2 tweets
    
    # 5. Analysis performed
    mock_analysis_engine.analyze.assert_called_once()
    
    # 6. Analysis saved
    mock_repo.save_analysis.assert_called_once()
    
    # 7. Document generated
    mock_doc_gen.generate.assert_called_once()
    
    # 8. Email sent
    mock_email_service.send_campaign_results.assert_called_once()
    
    # 9. Document uploaded to storage
    mock_storage_service.upload_document.assert_called_once()
    
    # 10. Status updated to completed
    final_update = mock_repo.update_status.call_args_list[-1]
    assert final_update[0][1] == "completed"
    assert "document_url" in final_update[1]
    assert "results_count" in final_update[1]


# ─── Test Error Handling and Retry Logic ─────────────────────────────────────


@patch('src.workers.campaign_executor.CampaignRepository')
@patch('src.workers.campaign_executor.get_supabase_client')
def test_campaign_not_found_error(
    mock_get_db,
    mock_campaign_repo_class,
    campaign_id
):
    """Test handling of campaign not found error"""
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    mock_repo = Mock()
    mock_campaign_repo_class.return_value = mock_repo
    mock_repo.get_by_id.return_value = None  # Campaign not found
    
    with pytest.raises(RuntimeError) as exc_info:
        execute_campaign(campaign_id)
    
    assert "not found" in str(exc_info.value).lower()
    
    # Verify status was updated to failed
    mock_repo.update_status.assert_called()
    assert mock_repo.update_status.call_args[0][1] == "failed"


@patch('src.workers.campaign_executor.ScrapingEngineFactory')
@patch('src.workers.campaign_executor.ConfigurationManager')
@patch('src.workers.campaign_executor.CampaignRepository')
@patch('src.workers.campaign_executor.get_supabase_client')
def test_scraping_failure_updates_status(
    mock_get_db,
    mock_campaign_repo_class,
    mock_config_mgr_class,
    mock_scraping_factory,
    campaign_id,
    realistic_campaign_record,
    realistic_configuration
):
    """Test that scraping failure updates campaign status to failed"""
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    mock_repo = Mock()
    mock_campaign_repo_class.return_value = mock_repo
    mock_repo.get_by_id.return_value = realistic_campaign_record
    
    mock_config_mgr = Mock()
    mock_config_mgr_class.return_value = mock_config_mgr
    mock_config_mgr.get_configuration.return_value = realistic_configuration
    
    # Mock scraping failure
    mock_scraping_engine = Mock()
    mock_scraping_factory.create.return_value = mock_scraping_engine
    mock_scraping_engine.scrape.side_effect = Exception("Scraping failed")
    
    with pytest.raises(Exception):
        execute_campaign(campaign_id)
    
    # Verify status was updated to failed with error message
    failed_update = [call for call in mock_repo.update_status.call_args_list 
                     if call[0][1] == "failed"]
    assert len(failed_update) > 0
    assert "error_message" in failed_update[0][1]


@patch('src.workers.campaign_executor.AnalysisEngine')
@patch('src.workers.campaign_executor.ScrapingEngineFactory')
@patch('src.workers.campaign_executor.ConfigurationManager')
@patch('src.workers.campaign_executor.CampaignRepository')
@patch('src.workers.campaign_executor.get_supabase_client')
def test_analysis_failure_updates_status(
    mock_get_db,
    mock_campaign_repo_class,
    mock_config_mgr_class,
    mock_scraping_factory,
    mock_analysis_engine_class,
    campaign_id,
    realistic_campaign_record,
    realistic_configuration,
    realistic_tweets
):
    """Test that analysis failure updates campaign status to failed"""
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    mock_repo = Mock()
    mock_campaign_repo_class.return_value = mock_repo
    mock_repo.get_by_id.return_value = realistic_campaign_record
    
    mock_config_mgr = Mock()
    mock_config_mgr_class.return_value = mock_config_mgr
    mock_config_mgr.get_configuration.return_value = realistic_configuration
    
    mock_scraping_engine = Mock()
    mock_scraping_factory.create.return_value = mock_scraping_engine
    mock_scraping_engine.scrape.return_value = realistic_tweets
    
    # Mock analysis failure
    mock_analysis_engine = Mock()
    mock_analysis_engine_class.return_value = mock_analysis_engine
    mock_analysis_engine.analyze.side_effect = RuntimeError("OpenAI API error")
    
    with pytest.raises(Exception):
        execute_campaign(campaign_id)
    
    # Verify status was updated to failed
    failed_update = [call for call in mock_repo.update_status.call_args_list 
                     if call[0][1] == "failed"]
    assert len(failed_update) > 0


@patch('src.workers.campaign_executor.EmailService')
@patch('src.workers.campaign_executor.DocumentGenerator')
@patch('src.workers.campaign_executor.AnalysisEngine')
@patch('src.workers.campaign_executor.ScrapingEngineFactory')
@patch('src.workers.campaign_executor.ConfigurationManager')
@patch('src.workers.campaign_executor.CampaignRepository')
@patch('src.workers.campaign_executor.get_supabase_client')
def test_email_failure_updates_status(
    mock_get_db,
    mock_campaign_repo_class,
    mock_config_mgr_class,
    mock_scraping_factory,
    mock_analysis_engine_class,
    mock_doc_gen_class,
    mock_email_service_class,
    campaign_id,
    realistic_campaign_record,
    realistic_configuration,
    realistic_tweets,
    realistic_analysis
):
    """Test that email failure updates campaign status to failed"""
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    mock_repo = Mock()
    mock_campaign_repo_class.return_value = mock_repo
    mock_repo.get_by_id.return_value = realistic_campaign_record
    
    mock_config_mgr = Mock()
    mock_config_mgr_class.return_value = mock_config_mgr
    mock_config_mgr.get_configuration.return_value = realistic_configuration
    
    mock_scraping_engine = Mock()
    mock_scraping_factory.create.return_value = mock_scraping_engine
    mock_scraping_engine.scrape.return_value = realistic_tweets
    
    mock_analysis_engine = Mock()
    mock_analysis_engine_class.return_value = mock_analysis_engine
    mock_analysis_engine.analyze.return_value = realistic_analysis
    
    mock_doc_gen = Mock()
    mock_doc_gen_class.return_value = mock_doc_gen
    mock_doc_gen.generate.return_value = "/tmp/results.docx"
    
    # Mock email failure
    mock_email_service = Mock()
    mock_email_service_class.return_value = mock_email_service
    mock_email_service.send_campaign_results.side_effect = RuntimeError("SMTP authentication failed")
    
    with pytest.raises(Exception):
        execute_campaign(campaign_id)
    
    # Verify status was updated to failed
    failed_update = [call for call in mock_repo.update_status.call_args_list 
                     if call[0][1] == "failed"]
    assert len(failed_update) > 0


# ─── Test Transient Error Detection ──────────────────────────────────────────


def test_is_transient_error_detects_timeout():
    """Test that timeout errors are detected as transient"""
    error = TimeoutError("Connection timeout")
    assert _is_transient_error(error) is True


def test_is_transient_error_detects_rate_limit():
    """Test that rate limit errors are detected as transient"""
    error = Exception("Rate limit exceeded")
    assert _is_transient_error(error) is True


def test_is_transient_error_detects_network_error():
    """Test that network errors are detected as transient"""
    error = Exception("Network connection failed")
    assert _is_transient_error(error) is True


def test_is_transient_error_detects_unavailable():
    """Test that service unavailable errors are detected as transient"""
    error = Exception("Service temporarily unavailable")
    assert _is_transient_error(error) is True


def test_is_transient_error_rejects_permanent_errors():
    """Test that permanent errors are not detected as transient"""
    error = ValueError("Invalid configuration")
    assert _is_transient_error(error) is False


def test_is_transient_error_rejects_authentication_errors():
    """Test that authentication errors are not transient"""
    error = Exception("Authentication failed")
    assert _is_transient_error(error) is False


# ─── Test Status Updates at Each Step ────────────────────────────────────────


@patch('src.workers.campaign_executor.ConfigurationManager')
@patch('src.workers.campaign_executor.CampaignRepository')
@patch('src.workers.campaign_executor.get_supabase_client')
def test_status_updated_to_running_first(
    mock_get_db,
    mock_campaign_repo_class,
    mock_config_mgr_class,
    campaign_id,
    realistic_campaign_record,
    realistic_configuration
):
    """Test that status is updated to running before any work"""
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    mock_repo = Mock()
    mock_campaign_repo_class.return_value = mock_repo
    mock_repo.get_by_id.return_value = realistic_campaign_record
    
    mock_config_mgr = Mock()
    mock_config_mgr_class.return_value = mock_config_mgr
    # Fail immediately after config retrieval
    mock_config_mgr.get_configuration.side_effect = Exception("Config error")
    
    with pytest.raises(Exception):
        execute_campaign(campaign_id)
    
    # Verify first update was to "running"
    first_update = mock_repo.update_status.call_args_list[0]
    assert first_update[0][0] == campaign_id
    assert first_update[0][1] == "running"


# ─── Test File Cleanup ───────────────────────────────────────────────────────


@patch('os.remove')
@patch('src.workers.campaign_executor.StorageService')
@patch('src.workers.campaign_executor.EmailService')
@patch('src.workers.campaign_executor.DocumentGenerator')
@patch('src.workers.campaign_executor.AnalysisEngine')
@patch('src.workers.campaign_executor.ScrapingEngineFactory')
@patch('src.workers.campaign_executor.ConfigurationManager')
@patch('src.workers.campaign_executor.CampaignRepository')
@patch('src.workers.campaign_executor.get_supabase_client')
def test_temporary_file_cleanup(
    mock_get_db,
    mock_campaign_repo_class,
    mock_config_mgr_class,
    mock_scraping_factory,
    mock_analysis_engine_class,
    mock_doc_gen_class,
    mock_email_service_class,
    mock_storage_service_class,
    mock_remove,
    campaign_id,
    realistic_campaign_record,
    realistic_configuration,
    realistic_tweets,
    realistic_analysis
):
    """Test that temporary document file is cleaned up after upload"""
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    mock_repo = Mock()
    mock_campaign_repo_class.return_value = mock_repo
    mock_repo.get_by_id.return_value = realistic_campaign_record
    
    mock_config_mgr = Mock()
    mock_config_mgr_class.return_value = mock_config_mgr
    mock_config_mgr.get_configuration.return_value = realistic_configuration
    
    mock_scraping_engine = Mock()
    mock_scraping_factory.create.return_value = mock_scraping_engine
    mock_scraping_engine.scrape.return_value = realistic_tweets
    
    mock_analysis_engine = Mock()
    mock_analysis_engine_class.return_value = mock_analysis_engine
    mock_analysis_engine.analyze.return_value = realistic_analysis
    
    mock_doc_gen = Mock()
    mock_doc_gen_class.return_value = mock_doc_gen
    doc_path = "/tmp/campaign_results.docx"
    mock_doc_gen.generate.return_value = doc_path
    
    mock_email_service = Mock()
    mock_email_service_class.return_value = mock_email_service
    
    mock_storage_service = Mock()
    mock_storage_service_class.return_value = mock_storage_service
    mock_storage_service.upload_document.return_value = "https://storage.example.com/doc.docx"
    
    execute_campaign(campaign_id)
    
    # Verify file was removed
    mock_remove.assert_called_once_with(doc_path)


@patch('os.remove')
@patch('src.workers.campaign_executor.StorageService')
@patch('src.workers.campaign_executor.EmailService')
@patch('src.workers.campaign_executor.DocumentGenerator')
@patch('src.workers.campaign_executor.AnalysisEngine')
@patch('src.workers.campaign_executor.ScrapingEngineFactory')
@patch('src.workers.campaign_executor.ConfigurationManager')
@patch('src.workers.campaign_executor.CampaignRepository')
@patch('src.workers.campaign_executor.get_supabase_client')
def test_file_cleanup_failure_handled_gracefully(
    mock_get_db,
    mock_campaign_repo_class,
    mock_config_mgr_class,
    mock_scraping_factory,
    mock_analysis_engine_class,
    mock_doc_gen_class,
    mock_email_service_class,
    mock_storage_service_class,
    mock_remove,
    campaign_id,
    realistic_campaign_record,
    realistic_configuration,
    realistic_tweets,
    realistic_analysis
):
    """Test that file cleanup failure doesn't fail the campaign"""
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    mock_repo = Mock()
    mock_campaign_repo_class.return_value = mock_repo
    mock_repo.get_by_id.return_value = realistic_campaign_record
    
    mock_config_mgr = Mock()
    mock_config_mgr_class.return_value = mock_config_mgr
    mock_config_mgr.get_configuration.return_value = realistic_configuration
    
    mock_scraping_engine = Mock()
    mock_scraping_factory.create.return_value = mock_scraping_engine
    mock_scraping_engine.scrape.return_value = realistic_tweets
    
    mock_analysis_engine = Mock()
    mock_analysis_engine_class.return_value = mock_analysis_engine
    mock_analysis_engine.analyze.return_value = realistic_analysis
    
    mock_doc_gen = Mock()
    mock_doc_gen_class.return_value = mock_doc_gen
    mock_doc_gen.generate.return_value = "/tmp/results.docx"
    
    mock_email_service = Mock()
    mock_email_service_class.return_value = mock_email_service
    
    mock_storage_service = Mock()
    mock_storage_service_class.return_value = mock_storage_service
    mock_storage_service.upload_document.return_value = "https://storage.example.com/doc.docx"
    
    # Mock file removal failure
    mock_remove.side_effect = OSError("Permission denied")
    
    # Should not raise an error
    execute_campaign(campaign_id)
    
    # Campaign should still be marked as completed
    final_update = mock_repo.update_status.call_args_list[-1]
    assert final_update[0][1] == "completed"
