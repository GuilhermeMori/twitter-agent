"""
Unit Tests for AnalysisEngine

Tests the OpenAI analysis prompt preparation and response parsing.
"""

import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

import json
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
import pytest

from src.models.campaign import Tweet
from src.models.analysis import Analysis
from src.services.analysis_engine import AnalysisEngine


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    return Mock()


@pytest.fixture
def analysis_engine(mock_openai_client):
    """Create an AnalysisEngine with mocked OpenAI client"""
    return AnalysisEngine(mock_openai_client)


@pytest.fixture
def sample_tweets():
    """Create sample tweets for testing"""
    return [
        Tweet(
            id="1",
            url="https://twitter.com/user1/status/1",
            author="user1",
            text="AI is transforming the world",
            likes=100,
            reposts=50,
            replies=20,
            timestamp=datetime.now(tz=timezone.utc),
        ),
        Tweet(
            id="2",
            url="https://twitter.com/user2/status/2",
            author="user2",
            text="Machine learning is the future",
            likes=200,
            reposts=80,
            replies=30,
            timestamp=datetime.now(tz=timezone.utc),
        ),
    ]


# ─── Test prepare_prompt ─────────────────────────────────────────────────────


def test_prepare_prompt_includes_tweet_count(analysis_engine, sample_tweets):
    """Test that prepare_prompt includes the tweet count"""
    prompt = analysis_engine.prepare_prompt(sample_tweets)

    assert "2 tweets" in prompt.lower()


def test_prepare_prompt_includes_tweet_authors(analysis_engine, sample_tweets):
    """Test that prepare_prompt includes tweet authors"""
    prompt = analysis_engine.prepare_prompt(sample_tweets)

    assert "@user1" in prompt
    assert "@user2" in prompt


def test_prepare_prompt_includes_tweet_text(analysis_engine, sample_tweets):
    """Test that prepare_prompt includes tweet text"""
    prompt = analysis_engine.prepare_prompt(sample_tweets)

    assert "AI is transforming the world" in prompt
    assert "Machine learning is the future" in prompt


def test_prepare_prompt_includes_engagement_metrics(analysis_engine, sample_tweets):
    """Test that prepare_prompt includes engagement metrics"""
    prompt = analysis_engine.prepare_prompt(sample_tweets)

    # Should include likes, reposts, replies
    assert "100" in prompt  # likes
    assert "50" in prompt  # reposts
    assert "20" in prompt  # replies


def test_prepare_prompt_caps_at_max_tweets(analysis_engine):
    """Test that prepare_prompt caps at maximum tweet count"""
    # Create 100 tweets
    many_tweets = [
        Tweet(
            id=str(i),
            url=f"https://twitter.com/user/status/{i}",
            author=f"user{i}",
            text=f"Tweet {i}",
            likes=10,
            reposts=5,
            replies=2,
            timestamp=datetime.now(tz=timezone.utc),
        )
        for i in range(100)
    ]

    prompt = analysis_engine.prepare_prompt(many_tweets)

    # Should cap at 50 tweets
    assert "50 tweets" in prompt.lower()
    assert "Tweet 49" in prompt  # 0-indexed, so 49 is the 50th
    assert "Tweet 50" not in prompt  # Should not include 51st tweet


def test_prepare_prompt_truncates_long_tweets(analysis_engine):
    """Test that prepare_prompt truncates very long tweets"""
    long_tweet = Tweet(
        id="1",
        url="https://twitter.com/user/status/1",
        author="user",
        text="a" * 500,  # 500 characters
        likes=10,
        reposts=5,
        replies=2,
        timestamp=datetime.now(tz=timezone.utc),
    )

    prompt = analysis_engine.prepare_prompt([long_tweet])

    # Should truncate to 280 characters
    assert "a" * 280 in prompt
    assert "a" * 281 not in prompt


def test_prepare_prompt_handles_empty_list(analysis_engine):
    """Test that prepare_prompt handles empty tweet list"""
    prompt = analysis_engine.prepare_prompt([])

    assert "0 tweets" in prompt.lower()


# ─── Test parse_response ─────────────────────────────────────────────────────


def test_parse_response_parses_valid_json(analysis_engine):
    """Test that parse_response parses valid JSON response"""
    json_response = json.dumps(
        {
            "summary": "Test summary",
            "key_themes": ["AI", "ML"],
            "sentiment": "positive",
            "top_influencers": ["@user1", "@user2"],
            "recommendations": ["Recommendation 1", "Recommendation 2"],
        }
    )

    analysis = analysis_engine.parse_response(json_response)

    assert isinstance(analysis, Analysis)
    assert analysis.summary == "Test summary"
    assert analysis.key_themes == ["AI", "ML"]
    assert analysis.sentiment == "positive"
    assert analysis.top_influencers == ["@user1", "@user2"]
    assert analysis.recommendations == ["Recommendation 1", "Recommendation 2"]


def test_parse_response_strips_markdown_fences(analysis_engine):
    """Test that parse_response strips markdown code fences"""
    json_response = """```json
{
    "summary": "Test summary",
    "key_themes": ["AI"],
    "sentiment": "positive",
    "top_influencers": [],
    "recommendations": []
}
```"""

    analysis = analysis_engine.parse_response(json_response)

    assert analysis.summary == "Test summary"
    assert analysis.key_themes == ["AI"]


def test_parse_response_handles_missing_fields(analysis_engine):
    """Test that parse_response handles missing fields with defaults"""
    json_response = json.dumps(
        {
            "summary": "Test summary"
            # Missing other fields
        }
    )

    analysis = analysis_engine.parse_response(json_response)

    assert analysis.summary == "Test summary"
    assert analysis.key_themes == []
    assert analysis.sentiment == "neutral"
    assert analysis.top_influencers == []
    assert analysis.recommendations == []


def test_parse_response_handles_invalid_json(analysis_engine):
    """Test that parse_response handles invalid JSON gracefully"""
    invalid_json = "This is not JSON"

    analysis = analysis_engine.parse_response(invalid_json)

    # Should return a fallback Analysis with the raw text as summary
    assert isinstance(analysis, Analysis)
    assert "This is not JSON" in analysis.summary
    assert analysis.key_themes == []
    assert analysis.sentiment == "neutral"


def test_parse_response_handles_empty_string(analysis_engine):
    """Test that parse_response handles empty string"""
    analysis = analysis_engine.parse_response("")

    assert isinstance(analysis, Analysis)
    assert analysis.summary == "Analysis unavailable."
    assert analysis.key_themes == []


def test_parse_response_handles_malformed_json(analysis_engine):
    """Test that parse_response handles malformed JSON"""
    malformed_json = '{"summary": "Test", "key_themes": [unclosed'

    analysis = analysis_engine.parse_response(malformed_json)

    # Should return fallback Analysis
    assert isinstance(analysis, Analysis)
    assert analysis.sentiment == "neutral"


def test_parse_response_truncates_long_fallback_summary(analysis_engine):
    """Test that parse_response truncates very long fallback summaries"""
    long_text = "a" * 1000

    analysis = analysis_engine.parse_response(long_text)

    # Should truncate to 500 characters
    assert len(analysis.summary) == 500
    assert analysis.summary == "a" * 500


# ─── Test analyze (integration with mocked OpenAI) ───────────────────────────


def test_analyze_returns_analysis_for_valid_tweets(
    analysis_engine, mock_openai_client, sample_tweets
):
    """Test that analyze returns Analysis for valid tweets"""
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "summary": "AI and ML are trending",
            "key_themes": ["AI", "ML"],
            "sentiment": "positive",
            "top_influencers": ["@user1"],
            "recommendations": ["Focus on AI content"],
        }
    )
    mock_openai_client.chat.completions.create.return_value = mock_response

    analysis = analysis_engine.analyze(sample_tweets)

    assert isinstance(analysis, Analysis)
    assert analysis.summary == "AI and ML are trending"
    assert "AI" in analysis.key_themes


def test_analyze_returns_empty_analysis_for_no_tweets(analysis_engine, mock_openai_client):
    """Test that analyze returns empty analysis when no tweets provided"""
    analysis = analysis_engine.analyze([])

    assert isinstance(analysis, Analysis)
    assert "No tweets" in analysis.summary
    assert analysis.key_themes == []

    # Should not call OpenAI
    mock_openai_client.chat.completions.create.assert_not_called()


def test_analyze_handles_openai_rate_limit_error(
    analysis_engine, mock_openai_client, sample_tweets
):
    """Test that analyze handles OpenAI rate limit errors"""
    from openai import RateLimitError

    mock_openai_client.chat.completions.create.side_effect = RateLimitError(
        "Rate limit exceeded", response=Mock(status_code=429), body=None
    )

    with pytest.raises(RuntimeError) as exc_info:
        analysis_engine.analyze(sample_tweets)

    assert "rate limit" in str(exc_info.value).lower()


def test_analyze_handles_openai_api_error(analysis_engine, mock_openai_client, sample_tweets):
    """Test that analyze handles OpenAI API errors"""
    from openai import APIError

    mock_openai_client.chat.completions.create.side_effect = APIError(
        "API error", request=Mock(), body=None
    )

    with pytest.raises(RuntimeError) as exc_info:
        analysis_engine.analyze(sample_tweets)

    assert "api error" in str(exc_info.value).lower()


def test_analyze_calls_openai_with_correct_parameters(
    analysis_engine, mock_openai_client, sample_tweets
):
    """Test that analyze calls OpenAI with correct parameters"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "summary": "Test",
            "key_themes": [],
            "sentiment": "neutral",
            "top_influencers": [],
            "recommendations": [],
        }
    )
    mock_openai_client.chat.completions.create.return_value = mock_response

    analysis_engine.analyze(sample_tweets)

    # Verify OpenAI was called with correct parameters
    call_args = mock_openai_client.chat.completions.create.call_args
    assert call_args[1]["model"] == "gpt-4o-mini"
    assert call_args[1]["temperature"] == 0.3
    assert call_args[1]["max_tokens"] == 1500
    assert len(call_args[1]["messages"]) == 2  # system + user
