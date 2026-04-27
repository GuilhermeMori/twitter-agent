"""
Integration Tests for OpenAI Service

Tests the complete analysis workflow with realistic mocked OpenAI responses.
Verifies prompt generation, API interaction, and response parsing.
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
def realistic_openai_response():
    """Realistic OpenAI API response"""
    return {
        "id": "chatcmpl-abc123",
        "object": "chat.completion",
        "created": 1705320000,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "summary": "The analyzed tweets reveal a strong focus on artificial intelligence and its transformative potential. Key discussions center around AI's impact on various industries, the importance of building innovative products, and the future of technology. The sentiment is overwhelmingly positive, with influencers expressing optimism about AI's capabilities.",
                        "key_themes": [
                            "Artificial Intelligence",
                            "Product Development",
                            "Technology Innovation",
                            "Future of Work",
                            "Machine Learning"
                        ],
                        "sentiment": "positive",
                        "top_influencers": [
                            "@elonmusk",
                            "@naval",
                            "@sama",
                            "@karpathy"
                        ],
                        "recommendations": [
                            "Focus content strategy on AI innovation and practical applications",
                            "Engage with top influencers discussing AI developments",
                            "Monitor emerging trends in machine learning and automation",
                            "Create content that bridges technical AI concepts with business value"
                        ]
                    })
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 450,
            "completion_tokens": 180,
            "total_tokens": 630
        }
    }


@pytest.fixture
def sample_tweets():
    """Sample tweets for analysis"""
    return [
        Tweet(
            id="1747123456789012345",
            url="https://twitter.com/elonmusk/status/1747123456789012345",
            author="elonmusk",
            text="AI will change everything. The future is now.",
            likes=15000,
            reposts=3000,
            replies=500,
            timestamp=datetime.now(tz=timezone.utc)
        ),
        Tweet(
            id="1747123456789012346",
            url="https://twitter.com/naval/status/1747123456789012346",
            author="naval",
            text="Building products is the ultimate form of leverage.",
            likes=8000,
            reposts=1500,
            replies=200,
            timestamp=datetime.now(tz=timezone.utc)
        ),
        Tweet(
            id="1747123456789012347",
            url="https://twitter.com/sama/status/1747123456789012347",
            author="sama",
            text="The pace of AI progress is accelerating exponentially.",
            likes=12000,
            reposts=2500,
            replies=400,
            timestamp=datetime.now(tz=timezone.utc)
        )
    ]


@pytest.fixture
def large_tweet_set():
    """Large set of tweets to test prompt capping"""
    return [
        Tweet(
            id=str(i),
            url=f"https://twitter.com/user{i}/status/{i}",
            author=f"user{i}",
            text=f"Tweet number {i} about AI and technology",
            likes=100 * i,
            reposts=50 * i,
            replies=10 * i,
            timestamp=datetime.now(tz=timezone.utc)
        )
        for i in range(100)
    ]


# ─── Test Complete Analysis Workflow ─────────────────────────────────────────


def test_complete_analysis_workflow(sample_tweets, realistic_openai_response):
    """Test complete analysis workflow with realistic OpenAI response"""
    # Mock OpenAI client
    mock_client = Mock()
    mock_completions = MagicMock()
    mock_client.chat.completions = mock_completions
    
    # Setup mock response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = realistic_openai_response["choices"][0]["message"]["content"]
    mock_completions.create.return_value = mock_response
    
    # Execute analysis
    engine = AnalysisEngine(mock_client)
    analysis = engine.analyze(sample_tweets)
    
    # Verify OpenAI was called with correct parameters
    mock_completions.create.assert_called_once()
    call_args = mock_completions.create.call_args[1]
    
    assert call_args["model"] == "gpt-4o-mini"
    assert call_args["temperature"] == 0.3
    assert call_args["max_tokens"] == 1500
    assert len(call_args["messages"]) == 2
    
    # Verify system message
    system_msg = call_args["messages"][0]
    assert system_msg["role"] == "system"
    assert "social media analyst" in system_msg["content"].lower()
    assert "JSON" in system_msg["content"]
    
    # Verify user message contains tweet data
    user_msg = call_args["messages"][1]
    assert user_msg["role"] == "user"
    assert "@elonmusk" in user_msg["content"]
    assert "@naval" in user_msg["content"]
    assert "AI will change everything" in user_msg["content"]
    
    # Verify analysis result
    assert isinstance(analysis, Analysis)
    assert "artificial intelligence" in analysis.summary.lower()
    assert len(analysis.key_themes) == 5
    assert "Artificial Intelligence" in analysis.key_themes
    assert analysis.sentiment == "positive"
    assert "@elonmusk" in analysis.top_influencers
    assert len(analysis.recommendations) == 4


def test_analysis_with_empty_tweets():
    """Test analysis with no tweets returns empty analysis"""
    mock_client = Mock()
    engine = AnalysisEngine(mock_client)
    
    analysis = engine.analyze([])
    
    # Should not call OpenAI
    mock_client.chat.completions.create.assert_not_called()
    
    # Should return empty analysis
    assert isinstance(analysis, Analysis)
    assert "No tweets" in analysis.summary
    assert analysis.key_themes == []
    assert analysis.sentiment == "neutral"
    assert analysis.top_influencers == []
    assert analysis.recommendations == []


def test_analysis_caps_tweet_count(large_tweet_set):
    """Test that analysis caps tweets at maximum limit"""
    mock_client = Mock()
    mock_completions = MagicMock()
    mock_client.chat.completions = mock_completions
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "summary": "Test summary",
        "key_themes": [],
        "sentiment": "neutral",
        "top_influencers": [],
        "recommendations": []
    })
    mock_completions.create.return_value = mock_response
    
    engine = AnalysisEngine(mock_client)
    analysis = engine.analyze(large_tweet_set)
    
    # Verify prompt was capped
    call_args = mock_completions.create.call_args[1]
    user_msg = call_args["messages"][1]["content"]
    
    # Should mention 50 tweets (the cap)
    assert "50 tweets" in user_msg.lower()
    # Should not include tweet 51 or higher
    assert "Tweet number 50" not in user_msg
    assert "Tweet number 51" not in user_msg


# ─── Test Error Scenarios ────────────────────────────────────────────────────


def test_openai_rate_limit_error(sample_tweets):
    """Test handling of OpenAI rate limit errors"""
    from openai import RateLimitError
    
    mock_client = Mock()
    mock_completions = MagicMock()
    mock_client.chat.completions = mock_completions
    
    mock_completions.create.side_effect = RateLimitError(
        "Rate limit exceeded. Please try again later.",
        response=Mock(status_code=429),
        body=None
    )
    
    engine = AnalysisEngine(mock_client)
    
    with pytest.raises(RuntimeError) as exc_info:
        engine.analyze(sample_tweets)
    
    assert "rate limit" in str(exc_info.value).lower()


def test_openai_api_error(sample_tweets):
    """Test handling of OpenAI API errors"""
    from openai import APIError
    
    mock_client = Mock()
    mock_completions = MagicMock()
    mock_client.chat.completions = mock_completions
    
    mock_completions.create.side_effect = APIError(
        "Internal server error",
        request=Mock(),
        body=None
    )
    
    engine = AnalysisEngine(mock_client)
    
    with pytest.raises(RuntimeError) as exc_info:
        engine.analyze(sample_tweets)
    
    assert "api error" in str(exc_info.value).lower()


def test_openai_authentication_error(sample_tweets):
    """Test handling of authentication errors"""
    from openai import AuthenticationError
    
    mock_client = Mock()
    mock_completions = MagicMock()
    mock_client.chat.completions = mock_completions
    
    mock_completions.create.side_effect = AuthenticationError(
        "Invalid API key",
        response=Mock(status_code=401),
        body=None
    )
    
    engine = AnalysisEngine(mock_client)
    
    with pytest.raises(Exception):
        engine.analyze(sample_tweets)


def test_invalid_json_response(sample_tweets):
    """Test handling of invalid JSON in OpenAI response"""
    mock_client = Mock()
    mock_completions = MagicMock()
    mock_client.chat.completions = mock_completions
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is not valid JSON"
    mock_completions.create.return_value = mock_response
    
    engine = AnalysisEngine(mock_client)
    analysis = engine.analyze(sample_tweets)
    
    # Should return fallback analysis
    assert isinstance(analysis, Analysis)
    assert "This is not valid JSON" in analysis.summary
    assert analysis.sentiment == "neutral"


def test_malformed_json_response(sample_tweets):
    """Test handling of malformed JSON response"""
    mock_client = Mock()
    mock_completions = MagicMock()
    mock_client.chat.completions = mock_completions
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"summary": "Test", "key_themes": [unclosed'
    mock_completions.create.return_value = mock_response
    
    engine = AnalysisEngine(mock_client)
    analysis = engine.analyze(sample_tweets)
    
    # Should return fallback analysis
    assert isinstance(analysis, Analysis)
    assert analysis.sentiment == "neutral"


def test_json_with_markdown_fences(sample_tweets):
    """Test handling of JSON wrapped in markdown code fences"""
    mock_client = Mock()
    mock_completions = MagicMock()
    mock_client.chat.completions = mock_completions
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = """```json
{
    "summary": "Test summary with markdown fences",
    "key_themes": ["AI", "ML"],
    "sentiment": "positive",
    "top_influencers": ["@user1"],
    "recommendations": ["Test recommendation"]
}
```"""
    mock_completions.create.return_value = mock_response
    
    engine = AnalysisEngine(mock_client)
    analysis = engine.analyze(sample_tweets)
    
    # Should strip markdown and parse correctly
    assert analysis.summary == "Test summary with markdown fences"
    assert analysis.key_themes == ["AI", "ML"]
    assert analysis.sentiment == "positive"


def test_empty_response_content(sample_tweets):
    """Test handling of empty response content"""
    mock_client = Mock()
    mock_completions = MagicMock()
    mock_client.chat.completions = mock_completions
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = ""
    mock_completions.create.return_value = mock_response
    
    engine = AnalysisEngine(mock_client)
    analysis = engine.analyze(sample_tweets)
    
    # Should return fallback analysis
    assert isinstance(analysis, Analysis)
    assert analysis.summary == "Analysis unavailable."


# ─── Test Prompt Construction ────────────────────────────────────────────────


def test_prompt_includes_all_tweet_data(sample_tweets):
    """Test that prompt includes all relevant tweet data"""
    mock_client = Mock()
    engine = AnalysisEngine(mock_client)
    
    prompt = engine.prepare_prompt(sample_tweets)
    
    # Verify tweet count
    assert "3 tweets" in prompt.lower()
    
    # Verify all authors are included
    assert "@elonmusk" in prompt
    assert "@naval" in prompt
    assert "@sama" in prompt
    
    # Verify tweet text is included
    assert "AI will change everything" in prompt
    assert "Building products" in prompt
    assert "pace of AI progress" in prompt
    
    # Verify engagement metrics are included
    assert "15000" in prompt  # likes
    assert "3000" in prompt   # reposts
    assert "500" in prompt    # replies


def test_prompt_truncates_long_tweets():
    """Test that prompt truncates very long tweets"""
    long_tweet = Tweet(
        id="123",
        url="https://twitter.com/user/status/123",
        author="testuser",
        text="a" * 500,  # 500 characters
        likes=100,
        reposts=50,
        replies=10,
        timestamp=datetime.now(tz=timezone.utc)
    )
    
    mock_client = Mock()
    engine = AnalysisEngine(mock_client)
    
    prompt = engine.prepare_prompt([long_tweet])
    
    # Should truncate to 280 characters
    assert "a" * 280 in prompt
    assert "a" * 281 not in prompt


def test_prompt_formatting_consistency():
    """Test that prompt formatting is consistent"""
    tweets = [
        Tweet(
            id=str(i),
            url=f"https://twitter.com/user{i}/status/{i}",
            author=f"user{i}",
            text=f"Tweet {i}",
            likes=100,
            reposts=50,
            replies=10,
            timestamp=datetime.now(tz=timezone.utc)
        )
        for i in range(5)
    ]
    
    mock_client = Mock()
    engine = AnalysisEngine(mock_client)
    
    prompt = engine.prepare_prompt(tweets)
    
    # Verify consistent formatting
    for i in range(5):
        assert f"@user{i}" in prompt
        assert f"Tweet {i}" in prompt
        # Verify engagement icons are present
        assert "❤️" in prompt or "♥" in prompt  # likes
        assert "🔁" in prompt  # retweets
        assert "💬" in prompt  # replies


# ─── Test Response Parsing ───────────────────────────────────────────────────


def test_parse_response_with_all_fields():
    """Test parsing response with all fields present"""
    mock_client = Mock()
    engine = AnalysisEngine(mock_client)
    
    response = json.dumps({
        "summary": "Comprehensive analysis summary",
        "key_themes": ["Theme 1", "Theme 2", "Theme 3"],
        "sentiment": "mixed",
        "top_influencers": ["@user1", "@user2", "@user3"],
        "recommendations": ["Rec 1", "Rec 2", "Rec 3", "Rec 4"]
    })
    
    analysis = engine.parse_response(response)
    
    assert analysis.summary == "Comprehensive analysis summary"
    assert len(analysis.key_themes) == 3
    assert analysis.sentiment == "mixed"
    assert len(analysis.top_influencers) == 3
    assert len(analysis.recommendations) == 4


def test_parse_response_with_missing_fields():
    """Test parsing response with missing optional fields"""
    mock_client = Mock()
    engine = AnalysisEngine(mock_client)
    
    response = json.dumps({
        "summary": "Minimal analysis"
        # Missing all other fields
    })
    
    analysis = engine.parse_response(response)
    
    assert analysis.summary == "Minimal analysis"
    assert analysis.key_themes == []
    assert analysis.sentiment == "neutral"
    assert analysis.top_influencers == []
    assert analysis.recommendations == []


def test_parse_response_with_different_sentiment_values():
    """Test parsing responses with different sentiment values"""
    mock_client = Mock()
    engine = AnalysisEngine(mock_client)
    
    sentiments = ["positive", "negative", "neutral", "mixed"]
    
    for sentiment in sentiments:
        response = json.dumps({
            "summary": "Test",
            "key_themes": [],
            "sentiment": sentiment,
            "top_influencers": [],
            "recommendations": []
        })
        
        analysis = engine.parse_response(response)
        assert analysis.sentiment == sentiment
