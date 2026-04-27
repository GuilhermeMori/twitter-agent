"""
Property-Based Tests for Query Construction

Tests the correctness properties 12-17 defined in design.md using Hypothesis.
These tests verify that the TwitterScrapingEngine's build_query() method
constructs correct Twitter search queries across a wide range of inputs.
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
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
import re

# Now safe to import after environment is set up
from src.services.scraping_engine import TwitterScrapingEngine
from src.models.campaign import ScrapingConfig, SearchType


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

# Strategy for generating language codes
language_strategy = st.sampled_from(["en", "pt", "es", "fr", "de", "ja", "ko", "zh"])

# Strategy for generating engagement counts
engagement_strategy = st.integers(min_value=0, max_value=1000)

# Strategy for generating hours_back
hours_back_strategy = st.integers(min_value=1, max_value=168)

# Strategy for generating profile-based scraping configs
@st.composite
def profile_scraping_config(draw):
    """Generate a valid profile-based scraping configuration"""
    profiles = draw(st.lists(username_strategy, min_size=1, max_size=10))
    return ScrapingConfig(
        search_type=SearchType.PROFILE,
        profiles=profiles,
        keywords=None,
        language=draw(language_strategy),
        min_likes=draw(engagement_strategy),
        min_retweets=draw(engagement_strategy),
        min_replies=draw(engagement_strategy),
        hours_back=draw(hours_back_strategy),
        apify_token="test-token"
    )

# Strategy for generating keyword-based scraping configs
@st.composite
def keyword_scraping_config(draw):
    """Generate a valid keyword-based scraping configuration"""
    keywords = draw(st.lists(keyword_strategy, min_size=1, max_size=10))
    return ScrapingConfig(
        search_type=SearchType.KEYWORDS,
        profiles=None,
        keywords=keywords,
        language=draw(language_strategy),
        min_likes=draw(engagement_strategy),
        min_retweets=draw(engagement_strategy),
        min_replies=draw(engagement_strategy),
        hours_back=draw(hours_back_strategy),
        apify_token="test-token"
    )


# ─── Property 12: Profile Query Construction ─────────────────────────────────


@given(config=profile_scraping_config())
@settings(max_examples=20, deadline=None)
def test_property_12_profile_query_construction(config):
    """
    **Validates: Requirements 5.2, 5.3**
    
    Property 12: Profile Query Construction
    
    For any list of profiles, the scraping engine SHALL construct a query 
    where each profile appears with the "from:" operator, and multiple 
    profiles are combined with "OR".
    """
    # Create engine with mock client
    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)
    
    # Build query
    query = engine.build_query(config)
    
    # Verify each profile appears with "from:" operator
    assert config.profiles is not None, "Profile config should have profiles"
    for profile in config.profiles:
        expected_term = f"from:{profile}"
        assert expected_term in query, \
            f"Query should contain '{expected_term}' for profile '{profile}'"
    
    # Verify profiles are combined with OR
    if len(config.profiles) > 1:
        # Check that OR appears between profile terms
        assert " OR " in query, "Multiple profiles should be joined with ' OR '"
        
        # Verify the profile section is correctly formatted
        profile_parts = [f"from:{handle}" for handle in config.profiles]
        expected_profile_section = " OR ".join(profile_parts)
        assert expected_profile_section in query, \
            f"Query should contain profile section: '{expected_profile_section}'"


# ─── Property 13: Keyword Query Construction ─────────────────────────────────


@given(config=keyword_scraping_config())
@settings(max_examples=20, deadline=None)
def test_property_13_keyword_query_construction(config):
    """
    **Validates: Requirements 5.4**
    
    Property 13: Keyword Query Construction
    
    For any list of keywords, the scraping engine SHALL construct a query 
    where keywords are combined with "OR" operator.
    """
    # Create engine with mock client
    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)
    
    # Build query
    query = engine.build_query(config)
    
    # Verify each keyword appears in the query
    assert config.keywords is not None, "Keyword config should have keywords"
    for keyword in config.keywords:
        assert keyword in query, \
            f"Query should contain keyword '{keyword}'"
    
    # Verify keywords are combined with OR
    if len(config.keywords) > 1:
        # Check that OR appears between keywords
        assert " OR " in query, "Multiple keywords should be joined with ' OR '"
        
        # Verify the keyword section is correctly formatted
        expected_keyword_section = " OR ".join(config.keywords)
        assert expected_keyword_section in query, \
            f"Query should contain keyword section: '{expected_keyword_section}'"


# ─── Property 14: Language Operator Always Present ───────────────────────────


@given(config=st.one_of(profile_scraping_config(), keyword_scraping_config()))
@settings(max_examples=20, deadline=None)
def test_property_14_language_operator_always_present(config):
    """
    **Validates: Requirements 5.5**
    
    Property 14: Language Operator Always Present
    
    For any scraping configuration with a language specified, the constructed 
    query SHALL contain the "lang:" operator with that language.
    """
    # Create engine with mock client
    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)
    
    # Build query
    query = engine.build_query(config)
    
    # Verify language operator is present
    expected_lang_operator = f"lang:{config.language}"
    assert expected_lang_operator in query, \
        f"Query should always contain language operator '{expected_lang_operator}'"
    
    # Verify it appears exactly once
    lang_count = query.count(f"lang:{config.language}")
    assert lang_count == 1, \
        f"Language operator should appear exactly once, found {lang_count} times"


# ─── Property 15: Conditional Min Faves Operator ─────────────────────────────


@given(config=st.one_of(profile_scraping_config(), keyword_scraping_config()))
@settings(max_examples=20, deadline=None)
def test_property_15_conditional_min_faves_operator(config):
    """
    **Validates: Requirements 5.6**
    
    Property 15: Conditional Min Faves Operator
    
    For any scraping configuration, the "min_faves:" operator SHALL be 
    present in the query if and only if min_likes > 0.
    """
    # Create engine with mock client
    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)
    
    # Build query
    query = engine.build_query(config)
    
    # Check if min_faves operator should be present
    if config.min_likes > 0:
        expected_operator = f"min_faves:{config.min_likes}"
        assert expected_operator in query, \
            f"Query should contain '{expected_operator}' when min_likes > 0"
    else:
        # Should NOT contain min_faves operator
        assert "min_faves:" not in query, \
            "Query should NOT contain 'min_faves:' when min_likes = 0"


# ─── Property 16: Conditional Min Replies Operator ───────────────────────────


@given(config=st.one_of(profile_scraping_config(), keyword_scraping_config()))
@settings(max_examples=20, deadline=None)
def test_property_16_conditional_min_replies_operator(config):
    """
    **Validates: Requirements 5.7**
    
    Property 16: Conditional Min Replies Operator
    
    For any scraping configuration, the "min_replies:" operator SHALL be 
    present in the query if and only if min_replies > 0.
    """
    # Create engine with mock client
    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)
    
    # Build query
    query = engine.build_query(config)
    
    # Check if min_replies operator should be present
    if config.min_replies > 0:
        expected_operator = f"min_replies:{config.min_replies}"
        assert expected_operator in query, \
            f"Query should contain '{expected_operator}' when min_replies > 0"
    else:
        # Should NOT contain min_replies operator
        assert "min_replies:" not in query, \
            "Query should NOT contain 'min_replies:' when min_replies = 0"


# ─── Property 17: Since Operator Date Calculation ────────────────────────────


@given(config=st.one_of(profile_scraping_config(), keyword_scraping_config()))
@settings(max_examples=20, deadline=None)
def test_property_17_since_operator_date_calculation(config):
    """
    **Validates: Requirements 5.8**
    
    Property 17: Since Operator Date Calculation
    
    For any scraping configuration with hours_back specified, the "since:" 
    operator SHALL contain a date that is exactly hours_back hours before 
    the current time.
    """
    # Create engine with mock client
    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)
    
    # Capture the current time before building query
    before_query = datetime.now(tz=timezone.utc)
    
    # Build query
    query = engine.build_query(config)
    
    # Capture the current time after building query
    after_query = datetime.now(tz=timezone.utc)
    
    # Verify since operator is present
    assert "since:" in query, "Query should contain 'since:' operator"
    
    # Extract the date from the query
    since_match = re.search(r'since:(\d{4}-\d{2}-\d{2})', query)
    assert since_match is not None, "Query should contain 'since:' with date format YYYY-MM-DD"
    
    since_date_str = since_match.group(1)
    since_date = datetime.strptime(since_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    
    # Calculate expected date range (accounting for query execution time)
    expected_since_before = before_query - timedelta(hours=config.hours_back)
    expected_since_after = after_query - timedelta(hours=config.hours_back)
    
    # The since date should be within the expected range (same day)
    # We compare dates only (not times) since the query uses date format
    expected_date_before = expected_since_before.date()
    expected_date_after = expected_since_after.date()
    actual_date = since_date.date()
    
    # The actual date should be one of the possible dates
    # (could be different if query execution spans midnight)
    possible_dates = {expected_date_before, expected_date_after}
    assert actual_date in possible_dates, \
        f"Since date {actual_date} should be within expected range {possible_dates} " \
        f"(hours_back={config.hours_back})"


# ─── Additional Property: Query Structure Validation ─────────────────────────


@given(config=st.one_of(profile_scraping_config(), keyword_scraping_config()))
@settings(max_examples=10, deadline=None)
def test_query_contains_all_required_operators(config):
    """
    Additional property: Verify that the query contains all required operators
    in the correct format.
    
    This is a comprehensive check that combines multiple properties.
    """
    # Create engine with mock client
    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)
    
    # Build query
    query = engine.build_query(config)
    
    # Query should not be empty
    assert query.strip(), "Query should not be empty"
    
    # Query should contain language operator
    assert f"lang:{config.language}" in query, "Query should contain language operator"
    
    # Query should contain since operator
    assert "since:" in query, "Query should contain since operator"
    
    # Query should contain search terms (profiles or keywords)
    if config.search_type == SearchType.PROFILE and config.profiles:
        assert any(f"from:{p}" in query for p in config.profiles), \
            "Profile query should contain at least one 'from:' operator"
    elif config.search_type == SearchType.KEYWORDS and config.keywords:
        assert any(k in query for k in config.keywords), \
            "Keyword query should contain at least one keyword"
    
    # Verify conditional operators
    if config.min_likes > 0:
        assert f"min_faves:{config.min_likes}" in query
    else:
        assert "min_faves:" not in query
    
    if config.min_replies > 0:
        assert f"min_replies:{config.min_replies}" in query
    else:
        assert "min_replies:" not in query


# ─── Additional Property: Query Operators Are Space-Separated ────────────────


@given(config=st.one_of(profile_scraping_config(), keyword_scraping_config()))
@settings(max_examples=10, deadline=None)
def test_query_operators_are_space_separated(config):
    """
    Additional property: Verify that query operators are properly separated
    by spaces for Twitter's search syntax.
    """
    # Create engine with mock client
    mock_client = Mock()
    engine = TwitterScrapingEngine(mock_client)
    
    # Build query
    query = engine.build_query(config)
    
    # Split query into parts
    parts = query.split()
    
    # Each part should be non-empty
    for part in parts:
        assert part.strip(), "Query parts should not be empty"
    
    # Verify that operators are not concatenated without spaces
    # (e.g., "lang:enfrom:user" is invalid, should be "lang:en from:user")
    operators = ["lang:", "from:", "min_faves:", "min_replies:", "since:"]
    for i, operator in enumerate(operators):
        if operator in query:
            # Find all occurrences of this operator
            for match in re.finditer(re.escape(operator), query):
                start = match.start()
                # Check that there's a space or start of string before operator
                # (unless it's part of an OR clause)
                if start > 0:
                    prev_char = query[start - 1]
                    # Previous char should be space or part of " OR "
                    assert prev_char in (' ', '\t'), \
                        f"Operator '{operator}' should be preceded by space at position {start}"
