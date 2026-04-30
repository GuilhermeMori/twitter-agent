"""
Unit Tests for CampaignParser

Tests the parsing and formatting methods for profiles, keywords,
and engagement filters.
"""

import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

import pytest
from src.services.campaign_parser import CampaignParser


# ─── Test parse_profiles ─────────────────────────────────────────────────────


def test_parse_profiles_splits_on_commas():
    """Test that parse_profiles splits on commas"""
    raw = "@elonmusk, @naval, @sama"
    result = CampaignParser.parse_profiles(raw)

    assert result == ["elonmusk", "naval", "sama"]


def test_parse_profiles_splits_on_newlines():
    """Test that parse_profiles splits on newlines"""
    raw = "@elonmusk\n@naval\n@sama"
    result = CampaignParser.parse_profiles(raw)

    assert result == ["elonmusk", "naval", "sama"]


def test_parse_profiles_splits_on_mixed_delimiters():
    """Test that parse_profiles handles mixed commas and newlines"""
    raw = "@elonmusk, @naval\n@sama"
    result = CampaignParser.parse_profiles(raw)

    assert result == ["elonmusk", "naval", "sama"]


def test_parse_profiles_removes_at_prefix():
    """Test that parse_profiles removes @ prefix"""
    raw = "@elonmusk, naval, @sama"
    result = CampaignParser.parse_profiles(raw)

    assert result == ["elonmusk", "naval", "sama"]


def test_parse_profiles_strips_whitespace():
    """Test that parse_profiles strips surrounding whitespace"""
    raw = "  @elonmusk  ,  naval  ,  @sama  "
    result = CampaignParser.parse_profiles(raw)

    assert result == ["elonmusk", "naval", "sama"]


def test_parse_profiles_removes_empty_items():
    """Test that parse_profiles removes empty items"""
    raw = "@elonmusk, , @naval, , @sama"
    result = CampaignParser.parse_profiles(raw)

    assert result == ["elonmusk", "naval", "sama"]


def test_parse_profiles_handles_empty_string():
    """Test that parse_profiles handles empty string"""
    raw = ""
    result = CampaignParser.parse_profiles(raw)

    assert result == []


def test_parse_profiles_handles_whitespace_only():
    """Test that parse_profiles handles whitespace-only string"""
    raw = "   ,  ,  \n  "
    result = CampaignParser.parse_profiles(raw)

    assert result == []


def test_parse_profiles_handles_multiple_at_signs():
    """Test that parse_profiles handles multiple @ signs"""
    raw = "@@elonmusk, @@@naval"
    result = CampaignParser.parse_profiles(raw)

    # Should strip all leading @ signs
    assert result == ["elonmusk", "naval"]


# ─── Test parse_keywords ─────────────────────────────────────────────────────


def test_parse_keywords_splits_on_commas():
    """Test that parse_keywords splits on commas"""
    raw = "AI, machine learning, LLM"
    result = CampaignParser.parse_keywords(raw)

    assert result == ["AI", "machine learning", "LLM"]


def test_parse_keywords_splits_on_newlines():
    """Test that parse_keywords splits on newlines"""
    raw = "AI\nmachine learning\nLLM"
    result = CampaignParser.parse_keywords(raw)

    assert result == ["AI", "machine learning", "LLM"]


def test_parse_keywords_splits_on_mixed_delimiters():
    """Test that parse_keywords handles mixed commas and newlines"""
    raw = "AI, machine learning\nLLM"
    result = CampaignParser.parse_keywords(raw)

    assert result == ["AI", "machine learning", "LLM"]


def test_parse_keywords_strips_whitespace():
    """Test that parse_keywords strips surrounding whitespace"""
    raw = "  AI  ,  machine learning  ,  LLM  "
    result = CampaignParser.parse_keywords(raw)

    assert result == ["AI", "machine learning", "LLM"]


def test_parse_keywords_preserves_internal_spaces():
    """Test that parse_keywords preserves spaces within keywords"""
    raw = "machine learning, artificial intelligence"
    result = CampaignParser.parse_keywords(raw)

    assert result == ["machine learning", "artificial intelligence"]


def test_parse_keywords_removes_empty_items():
    """Test that parse_keywords removes empty items"""
    raw = "AI, , machine learning, , LLM"
    result = CampaignParser.parse_keywords(raw)

    assert result == ["AI", "machine learning", "LLM"]


def test_parse_keywords_handles_empty_string():
    """Test that parse_keywords handles empty string"""
    raw = ""
    result = CampaignParser.parse_keywords(raw)

    assert result == []


def test_parse_keywords_handles_special_characters():
    """Test that parse_keywords preserves special characters"""
    raw = "#AI, @mentions, $crypto"
    result = CampaignParser.parse_keywords(raw)

    assert result == ["#AI", "@mentions", "$crypto"]


# ─── Test format_profiles ────────────────────────────────────────────────────


def test_format_profiles_adds_at_prefix():
    """Test that format_profiles adds @ prefix to each handle"""
    profiles = ["elonmusk", "naval", "sama"]
    result = CampaignParser.format_profiles(profiles)

    assert result == "@elonmusk, @naval, @sama"


def test_format_profiles_handles_empty_list():
    """Test that format_profiles handles empty list"""
    profiles = []
    result = CampaignParser.format_profiles(profiles)

    assert result == ""


def test_format_profiles_handles_single_profile():
    """Test that format_profiles handles single profile"""
    profiles = ["elonmusk"]
    result = CampaignParser.format_profiles(profiles)

    assert result == "@elonmusk"


# ─── Test format_keywords ────────────────────────────────────────────────────


def test_format_keywords_joins_with_commas():
    """Test that format_keywords joins keywords with commas"""
    keywords = ["AI", "machine learning", "LLM"]
    result = CampaignParser.format_keywords(keywords)

    assert result == "AI, machine learning, LLM"


def test_format_keywords_handles_empty_list():
    """Test that format_keywords handles empty list"""
    keywords = []
    result = CampaignParser.format_keywords(keywords)

    assert result == ""


def test_format_keywords_handles_single_keyword():
    """Test that format_keywords handles single keyword"""
    keywords = ["AI"]
    result = CampaignParser.format_keywords(keywords)

    assert result == "AI"


# ─── Test format_engagement_filters ──────────────────────────────────────────


def test_format_engagement_filters_with_all_filters():
    """Test format_engagement_filters with all filters set"""
    result = CampaignParser.format_engagement_filters(10, 5, 3)

    assert "10 likes" in result
    assert "5 retweets" in result
    assert "3 replies" in result


def test_format_engagement_filters_with_zero_likes():
    """Test format_engagement_filters with zero likes"""
    result = CampaignParser.format_engagement_filters(0, 5, 3)

    assert "Sem filtro de likes" in result
    assert "5 retweets" in result
    assert "3 replies" in result


def test_format_engagement_filters_with_zero_retweets():
    """Test format_engagement_filters with zero retweets"""
    result = CampaignParser.format_engagement_filters(10, 0, 3)

    assert "10 likes" in result
    assert "Sem filtro de retweets" in result
    assert "3 replies" in result


def test_format_engagement_filters_with_zero_replies():
    """Test format_engagement_filters with zero replies"""
    result = CampaignParser.format_engagement_filters(10, 5, 0)

    assert "10 likes" in result
    assert "5 retweets" in result
    assert "Sem filtro de replies" in result


def test_format_engagement_filters_with_all_zeros():
    """Test format_engagement_filters with all zeros"""
    result = CampaignParser.format_engagement_filters(0, 0, 0)

    assert "Sem filtro de likes" in result
    assert "Sem filtro de retweets" in result
    assert "Sem filtro de replies" in result


def test_format_engagement_filters_contains_separators():
    """Test that format_engagement_filters uses pipe separators"""
    result = CampaignParser.format_engagement_filters(10, 5, 3)

    assert " | " in result
    assert result.count(" | ") == 2  # Two separators for three parts
