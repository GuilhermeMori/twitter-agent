"""
Unit Tests for DocumentGenerator

Tests the document generation and formatting methods.
"""

import os
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
import pytest

from src.models.campaign import Campaign, CampaignStatus, CampaignConfig, SearchType, Tweet
from src.models.analysis import Analysis
from src.services.document_generator import DocumentGenerator


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def document_generator():
    """Create a DocumentGenerator instance"""
    return DocumentGenerator()


@pytest.fixture
def sample_campaign():
    """Create a sample campaign"""
    config = CampaignConfig(
        profiles=["elonmusk", "naval"],
        keywords=[],
        language="en",
        min_likes=10,
        min_retweets=5,
        min_replies=2,
        hours_back=24
    )
    
    return Campaign(
        id=uuid4(),
        name="Test Campaign",
        social_network="twitter",
        search_type="profile",
        status=CampaignStatus.COMPLETED,
        config=config,
        results_count=2,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
        completed_at=datetime.now(tz=timezone.utc)
    )


@pytest.fixture
def sample_tweets():
    """Create sample tweets"""
    return [
        Tweet(
            id="1",
            url="https://twitter.com/user1/status/1",
            author="user1",
            text="First test tweet",
            likes=100,
            reposts=50,
            replies=20,
            timestamp=datetime.now(tz=timezone.utc)
        ),
        Tweet(
            id="2",
            url="https://twitter.com/user2/status/2",
            author="user2",
            text="Second test tweet",
            likes=200,
            reposts=80,
            replies=30,
            timestamp=datetime.now(tz=timezone.utc)
        ),
    ]


@pytest.fixture
def sample_analysis():
    """Create a sample analysis"""
    return Analysis(
        summary="AI and ML are trending topics",
        key_themes=["AI", "Machine Learning", "Technology"],
        sentiment="positive",
        top_influencers=["@user1", "@user2"],
        recommendations=["Focus on AI content", "Engage with influencers"]
    )


# ─── Test generate ───────────────────────────────────────────────────────────


@patch('src.services.document_generator.Document')
@patch('tempfile.NamedTemporaryFile')
def test_generate_creates_document(mock_tempfile, mock_document_class, document_generator, sample_campaign, sample_tweets, sample_analysis):
    """Test that generate creates a document file"""
    mock_doc = MagicMock()
    mock_document_class.return_value = mock_doc
    
    mock_temp = MagicMock()
    mock_temp.name = "/tmp/test_campaign.docx"
    mock_tempfile.return_value = mock_temp
    
    file_path = document_generator.generate(sample_campaign, sample_tweets, sample_analysis)
    
    assert file_path == "/tmp/test_campaign.docx"
    mock_doc.save.assert_called_once_with("/tmp/test_campaign.docx")
    mock_temp.close.assert_called_once()


@patch('src.services.document_generator.Document')
@patch('tempfile.NamedTemporaryFile')
def test_generate_adds_all_sections(mock_tempfile, mock_document_class, document_generator, sample_campaign, sample_tweets, sample_analysis):
    """Test that generate adds all required sections"""
    mock_doc = MagicMock()
    mock_document_class.return_value = mock_doc
    
    mock_temp = MagicMock()
    mock_temp.name = "/tmp/test_campaign.docx"
    mock_tempfile.return_value = mock_temp
    
    document_generator.generate(sample_campaign, sample_tweets, sample_analysis)
    
    # Verify document methods were called
    assert mock_doc.add_heading.call_count >= 4  # Header + sections
    assert mock_doc.add_paragraph.call_count >= 1


@patch('src.services.document_generator.Document')
@patch('tempfile.NamedTemporaryFile')
def test_generate_handles_empty_tweets(mock_tempfile, mock_document_class, document_generator, sample_campaign, sample_analysis):
    """Test that generate handles empty tweet list"""
    mock_doc = MagicMock()
    mock_document_class.return_value = mock_doc
    
    mock_temp = MagicMock()
    mock_temp.name = "/tmp/test_campaign.docx"
    mock_tempfile.return_value = mock_temp
    
    file_path = document_generator.generate(sample_campaign, [], sample_analysis)
    
    assert file_path == "/tmp/test_campaign.docx"
    mock_doc.save.assert_called_once()


# ─── Test format_campaign_config ─────────────────────────────────────────────


def test_format_campaign_config_includes_search_type(document_generator, sample_campaign):
    """Test that format_campaign_config includes search type"""
    result = document_generator.format_campaign_config(sample_campaign)
    
    assert "Search Type" in result
    assert "profile" in result


def test_format_campaign_config_includes_profiles(document_generator, sample_campaign):
    """Test that format_campaign_config includes profiles"""
    result = document_generator.format_campaign_config(sample_campaign)
    
    assert "Profiles" in result
    assert "@elonmusk" in result
    assert "@naval" in result


def test_format_campaign_config_includes_language(document_generator, sample_campaign):
    """Test that format_campaign_config includes language"""
    result = document_generator.format_campaign_config(sample_campaign)
    
    assert "Language" in result
    assert "en" in result


def test_format_campaign_config_includes_filters(document_generator, sample_campaign):
    """Test that format_campaign_config includes engagement filters"""
    result = document_generator.format_campaign_config(sample_campaign)
    
    assert "Filters" in result
    assert "10 likes" in result or "10" in result


def test_format_campaign_config_includes_time_window(document_generator, sample_campaign):
    """Test that format_campaign_config includes time window"""
    result = document_generator.format_campaign_config(sample_campaign)
    
    assert "Time Window" in result
    assert "24" in result


def test_format_campaign_config_handles_keyword_search(document_generator, sample_campaign):
    """Test that format_campaign_config handles keyword search"""
    sample_campaign.search_type = "keywords"
    sample_campaign.config.profiles = []
    sample_campaign.config.keywords = ["AI", "ML"]
    
    result = document_generator.format_campaign_config(sample_campaign)
    
    assert "Keywords" in result
    assert "AI" in result
    assert "ML" in result


# ─── Test format_tweet ───────────────────────────────────────────────────────


def test_format_tweet_includes_author(document_generator, sample_tweets):
    """Test that format_tweet includes author"""
    result = document_generator.format_tweet(sample_tweets[0])
    
    assert "@user1" in result


def test_format_tweet_includes_engagement_metrics(document_generator, sample_tweets):
    """Test that format_tweet includes engagement metrics"""
    result = document_generator.format_tweet(sample_tweets[0])
    
    assert "100" in result  # likes
    assert "50" in result   # reposts
    assert "20" in result   # replies


def test_format_tweet_includes_timestamp(document_generator, sample_tweets):
    """Test that format_tweet includes timestamp"""
    result = document_generator.format_tweet(sample_tweets[0])
    
    # Should include date in some format
    assert any(char.isdigit() for char in result)


def test_format_tweet_truncates_long_text(document_generator):
    """Test that format_tweet truncates long tweet text"""
    long_tweet = Tweet(
        id="1",
        url="https://twitter.com/user/status/1",
        author="user",
        text="a" * 200,
        likes=10,
        reposts=5,
        replies=2,
        timestamp=datetime.now(tz=timezone.utc)
    )
    
    result = document_generator.format_tweet(long_tweet)
    
    # Should truncate to 100 characters
    assert "a" * 100 in result
    assert "a" * 101 not in result


def test_format_tweet_handles_empty_text(document_generator):
    """Test that format_tweet handles empty tweet text"""
    empty_tweet = Tweet(
        id="1",
        url="https://twitter.com/user/status/1",
        author="user",
        text="",
        likes=10,
        reposts=5,
        replies=2,
        timestamp=datetime.now(tz=timezone.utc)
    )
    
    result = document_generator.format_tweet(empty_tweet)
    
    # Should still include author and metrics
    assert "@user" in result
    assert "10" in result


# ─── Test _add_header (indirectly through generate) ──────────────────────────


@patch('src.services.document_generator.Document')
@patch('tempfile.NamedTemporaryFile')
def test_header_includes_campaign_name(mock_tempfile, mock_document_class, document_generator, sample_campaign, sample_tweets, sample_analysis):
    """Test that header includes campaign name"""
    mock_doc = MagicMock()
    mock_document_class.return_value = mock_doc
    
    mock_temp = MagicMock()
    mock_temp.name = "/tmp/test_campaign.docx"
    mock_tempfile.return_value = mock_temp
    
    document_generator.generate(sample_campaign, sample_tweets, sample_analysis)
    
    # Check that add_heading was called with campaign name
    heading_calls = [call for call in mock_doc.add_heading.call_args_list]
    assert any("Test Campaign" in str(call) for call in heading_calls)


# ─── Test _add_configuration_section (indirectly) ────────────────────────────


@patch('src.services.document_generator.Document')
@patch('tempfile.NamedTemporaryFile')
def test_configuration_section_added(mock_tempfile, mock_document_class, document_generator, sample_campaign, sample_tweets, sample_analysis):
    """Test that configuration section is added"""
    mock_doc = MagicMock()
    mock_document_class.return_value = mock_doc
    
    mock_temp = MagicMock()
    mock_temp.name = "/tmp/test_campaign.docx"
    mock_tempfile.return_value = mock_temp
    
    document_generator.generate(sample_campaign, sample_tweets, sample_analysis)
    
    # Check that add_table was called (for configuration)
    assert mock_doc.add_table.called


# ─── Test _add_tweets_section (indirectly) ───────────────────────────────────


@patch('src.services.document_generator.Document')
@patch('tempfile.NamedTemporaryFile')
def test_tweets_section_handles_no_tweets(mock_tempfile, mock_document_class, document_generator, sample_campaign, sample_analysis):
    """Test that tweets section handles empty tweet list"""
    mock_doc = MagicMock()
    mock_document_class.return_value = mock_doc
    
    mock_temp = MagicMock()
    mock_temp.name = "/tmp/test_campaign.docx"
    mock_tempfile.return_value = mock_temp
    
    document_generator.generate(sample_campaign, [], sample_analysis)
    
    # Should still add heading for tweets section
    heading_calls = [call for call in mock_doc.add_heading.call_args_list]
    assert any("Collected Tweets" in str(call) or "tweets" in str(call).lower() for call in heading_calls)


# ─── Test _add_analysis_section (indirectly) ─────────────────────────────────


@patch('src.services.document_generator.Document')
@patch('tempfile.NamedTemporaryFile')
def test_analysis_section_added(mock_tempfile, mock_document_class, document_generator, sample_campaign, sample_tweets, sample_analysis):
    """Test that analysis section is added"""
    mock_doc = MagicMock()
    mock_document_class.return_value = mock_doc
    
    mock_temp = MagicMock()
    mock_temp.name = "/tmp/test_campaign.docx"
    mock_tempfile.return_value = mock_temp
    
    document_generator.generate(sample_campaign, sample_tweets, sample_analysis)
    
    # Check that analysis heading was added
    heading_calls = [call for call in mock_doc.add_heading.call_args_list]
    assert any("Analysis" in str(call) for call in heading_calls)
