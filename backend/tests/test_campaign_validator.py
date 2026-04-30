"""
Unit Tests for CampaignValidator

Tests the validation logic for campaign creation requests.
"""

import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

import pytest
from src.models.campaign import CampaignCreateDTO, SearchType
from src.services.campaign_validator import CampaignValidator


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def validator():
    """Create a CampaignValidator instance"""
    return CampaignValidator()


@pytest.fixture
def valid_profile_campaign():
    """Create a valid profile search campaign"""
    return CampaignCreateDTO(
        name="Test Campaign",
        search_type=SearchType.PROFILE,
        profiles="@elonmusk, @naval",
        keywords="",
        language="en",
        min_likes=10,
        min_retweets=5,
        min_replies=2,
        hours_back=24,
    )


@pytest.fixture
def valid_keyword_campaign():
    """Create a valid keyword search campaign"""
    return CampaignCreateDTO(
        name="Test Campaign",
        search_type=SearchType.KEYWORDS,
        profiles="",
        keywords="AI, machine learning",
        language="en",
        min_likes=10,
        min_retweets=5,
        min_replies=2,
        hours_back=24,
    )


# ─── Test validate_create ────────────────────────────────────────────────────


def test_validate_create_accepts_valid_profile_campaign(validator, valid_profile_campaign):
    """Test that validate_create accepts a valid profile campaign"""
    result = validator.validate_create(valid_profile_campaign)

    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_create_accepts_valid_keyword_campaign(validator, valid_keyword_campaign):
    """Test that validate_create accepts a valid keyword campaign"""
    result = validator.validate_create(valid_keyword_campaign)

    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_create_rejects_empty_name(validator, valid_profile_campaign):
    """Test that validate_create rejects empty campaign name"""
    valid_profile_campaign.name = ""

    result = validator.validate_create(valid_profile_campaign)

    assert result.is_valid is False
    assert "name" in result.errors
    assert "empty" in result.errors["name"].lower()


def test_validate_create_rejects_whitespace_only_name(validator, valid_profile_campaign):
    """Test that validate_create rejects whitespace-only campaign name"""
    valid_profile_campaign.name = "   "

    result = validator.validate_create(valid_profile_campaign)

    assert result.is_valid is False
    assert "name" in result.errors


def test_validate_create_rejects_negative_likes(validator, valid_profile_campaign):
    """Test that validate_create rejects negative min_likes"""
    valid_profile_campaign.min_likes = -1

    result = validator.validate_create(valid_profile_campaign)

    assert result.is_valid is False
    assert "min_likes" in result.errors
    assert "non-negative" in result.errors["min_likes"].lower()


def test_validate_create_rejects_negative_retweets(validator, valid_profile_campaign):
    """Test that validate_create rejects negative min_retweets"""
    valid_profile_campaign.min_retweets = -5

    result = validator.validate_create(valid_profile_campaign)

    assert result.is_valid is False
    assert "min_retweets" in result.errors


def test_validate_create_rejects_negative_replies(validator, valid_profile_campaign):
    """Test that validate_create rejects negative min_replies"""
    valid_profile_campaign.min_replies = -10

    result = validator.validate_create(valid_profile_campaign)

    assert result.is_valid is False
    assert "min_replies" in result.errors


def test_validate_create_accepts_zero_engagement_filters(validator, valid_profile_campaign):
    """Test that validate_create accepts zero engagement filters"""
    valid_profile_campaign.min_likes = 0
    valid_profile_campaign.min_retweets = 0
    valid_profile_campaign.min_replies = 0

    result = validator.validate_create(valid_profile_campaign)

    assert result.is_valid is True


def test_validate_create_accumulates_multiple_errors(validator, valid_profile_campaign):
    """Test that validate_create accumulates multiple validation errors"""
    valid_profile_campaign.name = ""
    valid_profile_campaign.min_likes = -1
    valid_profile_campaign.min_retweets = -2

    result = validator.validate_create(valid_profile_campaign)

    assert result.is_valid is False
    assert len(result.errors) >= 3
    assert "name" in result.errors
    assert "min_likes" in result.errors
    assert "min_retweets" in result.errors


# ─── Test validate_search_config ─────────────────────────────────────────────


def test_validate_search_config_accepts_valid_profile_search(validator, valid_profile_campaign):
    """Test that validate_search_config accepts valid profile search"""
    result = validator.validate_search_config(valid_profile_campaign)

    assert result.is_valid is True


def test_validate_search_config_accepts_valid_keyword_search(validator, valid_keyword_campaign):
    """Test that validate_search_config accepts valid keyword search"""
    result = validator.validate_search_config(valid_keyword_campaign)

    assert result.is_valid is True


def test_validate_search_config_rejects_profile_search_without_profiles(
    validator, valid_profile_campaign
):
    """Test that validate_search_config rejects profile search without profiles"""
    valid_profile_campaign.profiles = ""

    result = validator.validate_search_config(valid_profile_campaign)

    assert result.is_valid is False
    assert "profiles" in result.errors
    assert "required" in result.errors["profiles"].lower()


def test_validate_search_config_rejects_profile_search_with_whitespace_only(
    validator, valid_profile_campaign
):
    """Test that validate_search_config rejects profile search with whitespace-only profiles"""
    valid_profile_campaign.profiles = "   "

    result = validator.validate_search_config(valid_profile_campaign)

    assert result.is_valid is False
    assert "profiles" in result.errors


def test_validate_search_config_rejects_profile_search_with_empty_after_parsing(
    validator, valid_profile_campaign
):
    """Test that validate_search_config rejects profiles that are empty after parsing"""
    valid_profile_campaign.profiles = ", , , "

    result = validator.validate_search_config(valid_profile_campaign)

    assert result.is_valid is False
    assert "profiles" in result.errors
    assert "parsing" in result.errors["profiles"].lower()


def test_validate_search_config_rejects_keyword_search_without_keywords(
    validator, valid_keyword_campaign
):
    """Test that validate_search_config rejects keyword search without keywords"""
    valid_keyword_campaign.keywords = ""

    result = validator.validate_search_config(valid_keyword_campaign)

    assert result.is_valid is False
    assert "keywords" in result.errors
    assert "required" in result.errors["keywords"].lower()


def test_validate_search_config_rejects_keyword_search_with_whitespace_only(
    validator, valid_keyword_campaign
):
    """Test that validate_search_config rejects keyword search with whitespace-only keywords"""
    valid_keyword_campaign.keywords = "   "

    result = validator.validate_search_config(valid_keyword_campaign)

    assert result.is_valid is False
    assert "keywords" in result.errors


def test_validate_search_config_rejects_keyword_search_with_empty_after_parsing(
    validator, valid_keyword_campaign
):
    """Test that validate_search_config rejects keywords that are empty after parsing"""
    valid_keyword_campaign.keywords = ", , , "

    result = validator.validate_search_config(valid_keyword_campaign)

    assert result.is_valid is False
    assert "keywords" in result.errors


# ─── Test validate_engagement_filters ────────────────────────────────────────


def test_validate_engagement_filters_accepts_positive_values(validator):
    """Test that validate_engagement_filters accepts positive values"""
    result = validator.validate_engagement_filters(10, 5, 3)

    assert result.is_valid is True


def test_validate_engagement_filters_accepts_zero_values(validator):
    """Test that validate_engagement_filters accepts zero values"""
    result = validator.validate_engagement_filters(0, 0, 0)

    assert result.is_valid is True


def test_validate_engagement_filters_rejects_negative_likes(validator):
    """Test that validate_engagement_filters rejects negative likes"""
    result = validator.validate_engagement_filters(-1, 5, 3)

    assert result.is_valid is False
    assert "min_likes" in result.errors


def test_validate_engagement_filters_rejects_negative_retweets(validator):
    """Test that validate_engagement_filters rejects negative retweets"""
    result = validator.validate_engagement_filters(10, -1, 3)

    assert result.is_valid is False
    assert "min_retweets" in result.errors


def test_validate_engagement_filters_rejects_negative_replies(validator):
    """Test that validate_engagement_filters rejects negative replies"""
    result = validator.validate_engagement_filters(10, 5, -1)

    assert result.is_valid is False
    assert "min_replies" in result.errors


def test_validate_engagement_filters_accumulates_multiple_errors(validator):
    """Test that validate_engagement_filters accumulates multiple errors"""
    result = validator.validate_engagement_filters(-1, -2, -3)

    assert result.is_valid is False
    assert len(result.errors) == 3
    assert "min_likes" in result.errors
    assert "min_retweets" in result.errors
    assert "min_replies" in result.errors
