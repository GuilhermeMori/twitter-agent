"""
Property-Based Tests for Parsing Operations

Tests the correctness properties defined in design.md using Hypothesis.
These tests verify that parsing operations maintain their invariants
across a wide range of inputs.
"""

# Set up environment variables BEFORE any imports that might load settings
import os
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-bytes-long!!")
os.environ.setdefault("DEBUG", "True")

from hypothesis import given, strategies as st, settings
import pytest

# Now safe to import after environment is set up
from src.services.campaign_parser import CampaignParser
from src.models.campaign import CampaignConfig


# ─── Hypothesis Strategies ───────────────────────────────────────────────────


# Strategy for generating valid Twitter usernames (alphanumeric + underscore)
username_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
    min_size=1,
    max_size=20
)

# Strategy for generating keyword strings (alphanumeric + spaces)
keyword_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip())  # Ensure at least one non-whitespace character

# Strategy for generating lists of items with various delimiters
def items_with_delimiters_strategy(item_strategy):
    """Generate a string of items separated by commas or newlines"""
    return st.lists(item_strategy, min_size=1, max_size=10).flatmap(
        lambda items: st.sampled_from([
            ", ".join(items),  # Comma-separated
            ",".join(items),   # Comma-separated without spaces
            "\n".join(items),  # Newline-separated
            ",\n".join(items), # Mixed delimiters
        ])
    )

# Strategy for generating non-empty strings with at least one non-whitespace character
non_empty_string_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "P", "Zs")),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip())  # Ensure at least one non-whitespace character

# Strategy for generating valid campaign configurations
campaign_config_strategy = st.builds(
    CampaignConfig,
    profiles=st.one_of(
        st.none(),
        st.lists(username_strategy, min_size=1, max_size=5)
    ),
    keywords=st.one_of(
        st.none(),
        st.lists(keyword_strategy, min_size=1, max_size=5)
    ),
    language=st.sampled_from(["en", "pt", "es", "fr", "de"]),
    min_likes=st.integers(min_value=0, max_value=1000),
    min_retweets=st.integers(min_value=0, max_value=1000),
    min_replies=st.integers(min_value=0, max_value=1000),
    hours_back=st.integers(min_value=1, max_value=168)
)


# ─── Property 7: Profile Parsing Removes @ Symbol ───────────────────────────


@given(username=username_strategy)
@settings(max_examples=20, deadline=None)
def test_property_7_profile_parsing_removes_at_symbol(username):
    """
    **Validates: Requirements 3.4, 20.7**
    
    Property 7: Profile Parsing Removes @ Symbol
    
    For any profile string (with or without @ prefix), parsing SHALL remove 
    the @ symbol and return the username only.
    """
    parser = CampaignParser()
    
    # Test with @ prefix
    with_at = f"@{username}"
    parsed_with_at = parser.parse_profiles(with_at)
    assert len(parsed_with_at) == 1, "Should parse single profile"
    assert parsed_with_at[0] == username, f"Should remove @ symbol: expected '{username}', got '{parsed_with_at[0]}'"
    assert not parsed_with_at[0].startswith("@"), "Parsed profile should not start with @"
    
    # Test without @ prefix
    without_at = username
    parsed_without_at = parser.parse_profiles(without_at)
    assert len(parsed_without_at) == 1, "Should parse single profile"
    assert parsed_without_at[0] == username, f"Should preserve username: expected '{username}', got '{parsed_without_at[0]}'"
    
    # Both should produce the same result
    assert parsed_with_at == parsed_without_at, "Parsing with or without @ should produce same result"


# ─── Property 8: Keyword Preservation ────────────────────────────────────────


@given(keyword=keyword_strategy)
@settings(max_examples=20, deadline=None)
def test_property_8_keyword_preservation(keyword):
    """
    **Validates: Requirements 3.5, 20.8**
    
    Property 8: Keyword Preservation
    
    For any keyword string, parsing SHALL preserve the exact text (after 
    trimming whitespace) without modification or expansion.
    """
    parser = CampaignParser()
    
    # Parse the keyword
    parsed = parser.parse_keywords(keyword)
    
    # Should return a list with one item
    assert len(parsed) == 1, "Should parse single keyword"
    
    # The parsed keyword should match the original (after trimming)
    expected = keyword.strip()
    assert parsed[0] == expected, f"Should preserve keyword exactly: expected '{expected}', got '{parsed[0]}'"
    
    # No modifications should be made (no case changes, no expansions, etc.)
    # The only allowed transformation is whitespace trimming
    if keyword == keyword.strip():
        assert parsed[0] == keyword, "Should preserve keyword without any modifications"


# ─── Property 10: List Parsing Handles Multiple Delimiters ──────────────────


@given(items=st.lists(username_strategy, min_size=1, max_size=10))
@settings(max_examples=20, deadline=None)
def test_property_10_list_parsing_handles_multiple_delimiters(items):
    """
    **Validates: Requirements 20.1, 20.2, 20.3, 20.4, 20.5, 20.6**
    
    Property 10: List Parsing Handles Multiple Delimiters
    
    For any string containing items separated by commas or newlines, parsing 
    SHALL correctly split into individual items, trim whitespace from each 
    item, and remove empty items.
    """
    parser = CampaignParser()
    
    # Test comma-separated
    comma_separated = ", ".join(items)
    parsed_comma = parser.parse_profiles(comma_separated)
    assert len(parsed_comma) == len(items), "Should parse all comma-separated items"
    assert parsed_comma == items, f"Should correctly parse comma-separated: expected {items}, got {parsed_comma}"
    
    # Test newline-separated
    newline_separated = "\n".join(items)
    parsed_newline = parser.parse_profiles(newline_separated)
    assert len(parsed_newline) == len(items), "Should parse all newline-separated items"
    assert parsed_newline == items, f"Should correctly parse newline-separated: expected {items}, got {parsed_newline}"
    
    # Test mixed delimiters
    mixed = ",\n".join(items)
    parsed_mixed = parser.parse_profiles(mixed)
    assert len(parsed_mixed) == len(items), "Should parse all items with mixed delimiters"
    assert parsed_mixed == items, f"Should correctly parse mixed delimiters: expected {items}, got {parsed_mixed}"
    
    # Test with extra whitespace
    with_whitespace = " , ".join(items)
    parsed_whitespace = parser.parse_profiles(with_whitespace)
    assert len(parsed_whitespace) == len(items), "Should parse all items and trim whitespace"
    assert parsed_whitespace == items, f"Should correctly trim whitespace: expected {items}, got {parsed_whitespace}"


# ─── Property 11: Parsed List Is Never Empty After Valid Input ──────────────


@given(input_string=non_empty_string_strategy)
@settings(max_examples=20, deadline=None)
def test_property_11_parsed_list_is_never_empty_after_valid_input(input_string):
    """
    **Validates: Requirements 20.9**
    
    Property 11: Parsed List Is Never Empty After Valid Input
    
    For any non-empty input string containing at least one non-whitespace 
    character, parsing SHALL produce a non-empty list.
    """
    parser = CampaignParser()
    
    # Parse as profiles
    parsed_profiles = parser.parse_profiles(input_string)
    assert len(parsed_profiles) > 0, f"Should produce non-empty list for profiles: input='{input_string}'"
    
    # Parse as keywords
    parsed_keywords = parser.parse_keywords(input_string)
    assert len(parsed_keywords) > 0, f"Should produce non-empty list for keywords: input='{input_string}'"
    
    # All parsed items should be non-empty
    for item in parsed_profiles:
        assert item.strip(), "Parsed profile items should not be empty or whitespace-only"
    
    for item in parsed_keywords:
        assert item.strip(), "Parsed keyword items should not be empty or whitespace-only"


# ─── Property 21: Configuration Formatting Is Reversible ─────────────────────


@given(config=campaign_config_strategy)
@settings(max_examples=20, deadline=None)
def test_property_21_configuration_formatting_is_reversible(config):
    """
    **Validates: Requirements 22.1**
    
    Property 21: Configuration Formatting Is Reversible
    
    For any valid campaign configuration, parsing the configuration, formatting 
    it for display, and parsing again SHALL produce an equivalent configuration.
    """
    parser = CampaignParser()
    
    # Test profiles round-trip (if profiles exist)
    if config.profiles:
        # Format profiles for display
        formatted_profiles = parser.format_profiles(config.profiles)
        
        # Parse the formatted string back
        reparsed_profiles = parser.parse_profiles(formatted_profiles)
        
        # Should match the original
        assert reparsed_profiles == config.profiles, \
            f"Profile round-trip failed: original={config.profiles}, formatted='{formatted_profiles}', reparsed={reparsed_profiles}"
    
    # Test keywords round-trip (if keywords exist)
    if config.keywords:
        # Format keywords for display
        formatted_keywords = parser.format_keywords(config.keywords)
        
        # Parse the formatted string back
        reparsed_keywords = parser.parse_keywords(formatted_keywords)
        
        # Should match the original
        assert reparsed_keywords == config.keywords, \
            f"Keyword round-trip failed: original={config.keywords}, formatted='{formatted_keywords}', reparsed={reparsed_keywords}"


# ─── Additional Property: Empty Input Produces Empty List ────────────────────


@given(empty_input=st.sampled_from(["", "   ", "\t", "\n", "  \t\n  ", ",,,", "\n\n\n"]))
@settings(max_examples=10, deadline=None)
def test_empty_input_produces_empty_list(empty_input):
    """
    Additional property: Empty or whitespace-only input should produce an 
    empty list after parsing.
    
    This is the complement to Property 11.
    """
    parser = CampaignParser()
    
    # Parse as profiles
    parsed_profiles = parser.parse_profiles(empty_input)
    assert len(parsed_profiles) == 0, f"Empty input should produce empty list for profiles: input='{empty_input}'"
    
    # Parse as keywords
    parsed_keywords = parser.parse_keywords(empty_input)
    assert len(parsed_keywords) == 0, f"Empty input should produce empty list for keywords: input='{empty_input}'"


# ─── Additional Property: Multiple @ Symbols Are Handled ─────────────────────


@given(username=username_strategy, at_count=st.integers(min_value=1, max_value=5))
@settings(max_examples=10, deadline=None)
def test_multiple_at_symbols_are_stripped(username, at_count):
    """
    Additional property: Multiple @ symbols at the start should all be removed.
    
    This tests edge cases like "@@@@username".
    """
    parser = CampaignParser()
    
    # Create a profile with multiple @ symbols
    multiple_at = ("@" * at_count) + username
    
    # Parse it
    parsed = parser.parse_profiles(multiple_at)
    
    # Should have one item
    assert len(parsed) == 1, "Should parse single profile"
    
    # All @ symbols should be removed
    assert parsed[0] == username, f"Should remove all @ symbols: expected '{username}', got '{parsed[0]}'"
    assert not parsed[0].startswith("@"), "Parsed profile should not start with @"


# ─── Additional Property: Formatting Adds @ Prefix ───────────────────────────


@given(profiles=st.lists(username_strategy, min_size=1, max_size=5))
@settings(max_examples=10, deadline=None)
def test_formatting_adds_at_prefix(profiles):
    """
    Additional property: Formatting profiles should add @ prefix to each profile.
    """
    parser = CampaignParser()
    
    # Format the profiles
    formatted = parser.format_profiles(profiles)
    
    # Each profile should appear with @ prefix
    for profile in profiles:
        assert f"@{profile}" in formatted, f"Formatted string should contain '@{profile}'"
    
    # Should be comma-separated
    expected = ", ".join(f"@{p}" for p in profiles)
    assert formatted == expected, f"Should format as comma-separated with @ prefix: expected '{expected}', got '{formatted}'"
