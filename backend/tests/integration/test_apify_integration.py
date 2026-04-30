"""
Integration Tests for Apify Service

Tests the complete scraping workflow with realistic mocked Apify responses.
Verifies query construction, actor invocation, and result transformation.
"""

import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
import pytest

from src.models.campaign import ScrapingConfig, SearchType
from src.services.scraping_engine import TwitterScrapingEngine, ScrapingEngineFactory


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def realistic_apify_response():
    """Realistic Apify actor response with tweet data"""
    return {
        "defaultDatasetId": "dataset-abc123",
        "status": "SUCCEEDED",
        "startedAt": "2024-01-15T10:00:00.000Z",
        "finishedAt": "2024-01-15T10:05:00.000Z",
    }


@pytest.fixture
def realistic_tweet_data():
    """Realistic tweet data from Apify dataset"""
    return [
        {
            "id": "1747123456789012345",
            "url": "https://twitter.com/elonmusk/status/1747123456789012345",
            "author": {"userName": "elonmusk", "name": "Elon Musk", "isVerified": True},
            "text": "AI will change everything. The future is now.",
            "likeCount": 15000,
            "retweetCount": 3000,
            "replyCount": 500,
            "createdAt": "2024-01-15T09:30:00.000Z",
            "lang": "en",
        },
        {
            "id": "1747123456789012346",
            "url": "https://twitter.com/naval/status/1747123456789012346",
            "author": {"userName": "naval", "name": "Naval", "isVerified": True},
            "text": "Building products is the ultimate form of leverage.",
            "likeCount": 8000,
            "retweetCount": 1500,
            "replyCount": 200,
            "createdAt": "2024-01-15T08:45:00.000Z",
            "lang": "en",
        },
        {
            "id": "1747123456789012347",
            "url": "https://twitter.com/elonmusk/status/1747123456789012347",
            "author": {"userName": "elonmusk", "name": "Elon Musk", "isVerified": True},
            "text": "Short tweet with low engagement",
            "likeCount": 5,  # Below threshold
            "retweetCount": 2,
            "replyCount": 1,
            "createdAt": "2024-01-15T07:00:00.000Z",
            "lang": "en",
        },
    ]


@pytest.fixture
def profile_scraping_config():
    """Profile-based scraping configuration"""
    return ScrapingConfig(
        search_type=SearchType.PROFILE,
        profiles=["elonmusk", "naval"],
        keywords=[],
        language="en",
        min_likes=100,
        min_retweets=50,
        min_replies=10,
        hours_back=24,
        apify_token="apify_test_token_12345",
        twitter_auth_token="test_auth_token",
        twitter_ct0="test_ct0_token",
    )


@pytest.fixture
def keyword_scraping_config():
    """Keyword-based scraping configuration"""
    return ScrapingConfig(
        search_type=SearchType.KEYWORDS,
        profiles=[],
        keywords=["AI", "machine learning", "deep learning"],
        language="en",
        min_likes=50,
        min_retweets=20,
        min_replies=5,
        hours_back=48,
        apify_token="apify_test_token_12345",
        twitter_auth_token=None,
        twitter_ct0=None,
    )


# ─── Test Complete Scraping Workflow ─────────────────────────────────────────


def test_complete_profile_scraping_workflow(
    profile_scraping_config, realistic_apify_response, realistic_tweet_data
):
    """Test complete scraping workflow for profile search"""
    # Mock Apify client
    mock_client = Mock()
    mock_actor = MagicMock()
    mock_dataset = MagicMock()

    # Setup mock chain
    mock_client.actor.return_value = mock_actor
    mock_actor.call.return_value = realistic_apify_response
    mock_client.dataset.return_value = mock_dataset
    mock_dataset.iterate_items.return_value = iter(realistic_tweet_data)

    # Execute scraping
    engine = TwitterScrapingEngine(mock_client)
    tweets = engine.scrape(profile_scraping_config)

    # Verify actor was called with correct parameters
    mock_client.actor.assert_called_once_with("automation-lab/twitter-scraper")
    call_args = mock_actor.call.call_args[1]["run_input"]

    assert "searchTerms" in call_args
    assert len(call_args["searchTerms"]) == 1
    assert "from:elonmusk" in call_args["searchTerms"][0]
    assert "from:naval" in call_args["searchTerms"][0]
    assert call_args["maxItems"] == 200
    assert call_args["queryType"] == "Latest"

    # Verify Twitter cookies were included
    assert "cookies" in call_args
    assert len(call_args["cookies"]) == 2
    assert call_args["cookies"][0]["name"] == "auth_token"
    assert call_args["cookies"][1]["name"] == "ct0"

    # Verify dataset was fetched
    mock_client.dataset.assert_called_once_with("dataset-abc123")
    mock_dataset.iterate_items.assert_called_once()

    # Verify filtering: only 2 tweets should pass (3rd has low engagement)
    assert len(tweets) == 2
    assert all(t.likes >= 100 for t in tweets)
    assert all(t.reposts >= 50 for t in tweets)
    assert all(t.replies >= 10 for t in tweets)


def test_complete_keyword_scraping_workflow(
    keyword_scraping_config, realistic_apify_response, realistic_tweet_data
):
    """Test complete scraping workflow for keyword search"""
    # Mock Apify client
    mock_client = Mock()
    mock_actor = MagicMock()
    mock_dataset = MagicMock()

    # Setup mock chain
    mock_client.actor.return_value = mock_actor
    mock_actor.call.return_value = realistic_apify_response
    mock_client.dataset.return_value = mock_dataset
    mock_dataset.iterate_items.return_value = iter(realistic_tweet_data)

    # Execute scraping
    engine = TwitterScrapingEngine(mock_client)
    tweets = engine.scrape(keyword_scraping_config)

    # Verify query construction for keywords
    call_args = mock_actor.call.call_args[1]["run_input"]
    query = call_args["searchTerms"][0]

    assert "AI OR machine learning OR deep learning" in query
    assert "lang:en" in query
    assert "min_faves:50" in query
    assert "min_replies:5" in query
    assert "since:" in query

    # Verify no cookies when not provided
    assert "cookies" not in call_args

    # Verify results
    assert len(tweets) == 2  # Filtered by engagement thresholds


# ─── Test Error Scenarios ────────────────────────────────────────────────────


def test_apify_actor_failure(profile_scraping_config):
    """Test handling of Apify actor failure"""
    mock_client = Mock()
    mock_actor = MagicMock()

    mock_client.actor.return_value = mock_actor
    mock_actor.call.side_effect = Exception("Actor execution failed")

    engine = TwitterScrapingEngine(mock_client)

    with pytest.raises(Exception) as exc_info:
        engine.scrape(profile_scraping_config)

    assert "Actor execution failed" in str(exc_info.value)


def test_empty_dataset_results(profile_scraping_config, realistic_apify_response):
    """Test handling of empty dataset (no tweets found)"""
    mock_client = Mock()
    mock_actor = MagicMock()
    mock_dataset = MagicMock()

    mock_client.actor.return_value = mock_actor
    mock_actor.call.return_value = realistic_apify_response
    mock_client.dataset.return_value = mock_dataset
    mock_dataset.iterate_items.return_value = iter([])  # Empty results

    engine = TwitterScrapingEngine(mock_client)
    tweets = engine.scrape(profile_scraping_config)

    assert len(tweets) == 0


def test_malformed_tweet_data_handling(profile_scraping_config, realistic_apify_response):
    """Test handling of malformed tweet data"""
    malformed_data = [
        {
            "id": "123",
            "url": "https://twitter.com/user/status/123",
            # Missing author, text, engagement counts
        },
        {
            # Completely empty tweet
        },
        {
            "id": "456",
            "url": "https://twitter.com/user/status/456",
            "author": {"userName": "testuser"},
            "text": "Valid tweet",
            "likeCount": 1000,
            "retweetCount": 500,
            "replyCount": 100,
            "createdAt": "2024-01-15T10:00:00.000Z",
        },
    ]

    mock_client = Mock()
    mock_actor = MagicMock()
    mock_dataset = MagicMock()

    mock_client.actor.return_value = mock_actor
    mock_actor.call.return_value = realistic_apify_response
    mock_client.dataset.return_value = mock_dataset
    mock_dataset.iterate_items.return_value = iter(malformed_data)

    engine = TwitterScrapingEngine(mock_client)
    tweets = engine.scrape(profile_scraping_config)

    # Should handle malformed data gracefully
    # At least the valid tweet should be included
    assert len(tweets) >= 1


def test_network_timeout_error(profile_scraping_config):
    """Test handling of network timeout during actor execution"""
    mock_client = Mock()
    mock_actor = MagicMock()

    mock_client.actor.return_value = mock_actor
    mock_actor.call.side_effect = TimeoutError("Network timeout")

    engine = TwitterScrapingEngine(mock_client)

    with pytest.raises(TimeoutError):
        engine.scrape(profile_scraping_config)


def test_rate_limit_error(profile_scraping_config):
    """Test handling of rate limit errors"""
    mock_client = Mock()
    mock_actor = MagicMock()

    mock_client.actor.return_value = mock_actor
    mock_actor.call.side_effect = Exception("Rate limit exceeded")

    engine = TwitterScrapingEngine(mock_client)

    with pytest.raises(Exception) as exc_info:
        engine.scrape(profile_scraping_config)

    assert "rate limit" in str(exc_info.value).lower()


# ─── Test Query Construction Integration ─────────────────────────────────────


def test_query_construction_with_all_filters(profile_scraping_config):
    """Test that query includes all specified filters"""
    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)

    query = engine.build_query(profile_scraping_config)

    # Verify all components are present
    assert "from:elonmusk OR from:naval" in query
    assert "lang:en" in query
    assert "min_faves:100" in query
    assert "min_replies:10" in query
    assert "since:" in query

    # Note: min_retweets is not a Twitter search operator
    # The engine applies this filter locally


def test_query_construction_without_optional_filters():
    """Test query construction with minimal filters"""
    config = ScrapingConfig(
        search_type=SearchType.PROFILE,
        profiles=["testuser"],
        keywords=[],
        language="en",
        min_likes=0,  # No minimum
        min_retweets=0,
        min_replies=0,
        hours_back=24,
        apify_token="test_token",
        twitter_auth_token=None,
        twitter_ct0=None,
    )

    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)

    query = engine.build_query(config)

    # Should not include min_faves or min_replies when 0
    assert "min_faves" not in query
    assert "min_replies" not in query
    # But should still include required filters
    assert "from:testuser" in query
    assert "lang:en" in query
    assert "since:" in query


# ─── Test Result Transformation Integration ──────────────────────────────────


def test_result_transformation_preserves_all_fields(realistic_tweet_data):
    """Test that transformation preserves all tweet fields"""
    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)

    tweets = engine.transform_results(realistic_tweet_data[:1])

    assert len(tweets) == 1
    tweet = tweets[0]

    assert tweet.id == "1747123456789012345"
    assert tweet.url == "https://twitter.com/elonmusk/status/1747123456789012345"
    assert tweet.author == "elonmusk"
    assert tweet.text == "AI will change everything. The future is now."
    assert tweet.likes == 15000
    assert tweet.reposts == 3000
    assert tweet.replies == 500
    assert tweet.timestamp is not None


def test_result_transformation_handles_alternative_field_names():
    """Test transformation with alternative Apify field names"""
    alternative_format = [
        {
            "tweetId": "123",
            "tweetUrl": "https://twitter.com/user/status/123",
            "username": "testuser",
            "fullText": "Test tweet",
            "likes": 100,
            "retweets": 50,
            "replies": 10,
            "timestamp": "2024-01-15T10:00:00.000Z",
        }
    ]

    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)

    tweets = engine.transform_results(alternative_format)

    assert len(tweets) == 1
    assert tweets[0].id == "123"
    assert tweets[0].author == "testuser"
    assert tweets[0].text == "Test tweet"


# ─── Test Factory Integration ────────────────────────────────────────────────


def test_factory_creates_engine_with_apify_client():
    """Test that factory creates engine with properly configured Apify client"""
    engine = ScrapingEngineFactory.create("twitter", "test_apify_token")

    assert isinstance(engine, TwitterScrapingEngine)
    assert engine._client is not None


def test_factory_rejects_unsupported_networks():
    """Test that factory rejects unsupported social networks"""
    with pytest.raises(ValueError) as exc_info:
        ScrapingEngineFactory.create("facebook", "test_token")

    assert "unsupported" in str(exc_info.value).lower()
