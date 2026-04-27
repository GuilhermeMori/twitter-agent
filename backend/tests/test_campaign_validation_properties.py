"""
Property-Based Tests for Campaign Validation

Tests the correctness properties defined in design.md using Hypothesis.
These tests verify that campaign validation rules maintain their invariants
across a wide range of inputs.
"""

from hypothesis import given, strategies as st, settings
import pytest

# Import models directly (no settings dependency)
from src.models.campaign import CampaignCreateDTO, SearchType, ValidationResult


# ─── Hypothesis Strategies ───────────────────────────────────────────────────


def get_validator():
    """Get CampaignValidator instance - import delayed to avoid settings issues"""
    from src.services.campaign_validator import CampaignValidator
    return CampaignValidator()


# Strategy for generating valid campaign names
valid_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "P", "Zs")),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip())  # Ensure at least one non-whitespace character

# Strategy for generating empty or whitespace-only strings
empty_or_whitespace_strategy = st.one_of(
    st.just(""),
    st.just("   "),
    st.just("\t"),
    st.just("\n"),
    st.just("\t\n  "),
    st.just("     \t\n     ")
)

# Strategy for generating profile strings (comma or newline separated)
profile_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
    min_size=1,
    max_size=20
)

profiles_list_strategy = st.lists(profile_strategy, min_size=1, max_size=10).map(
    lambda profiles: ", ".join(f"@{p}" for p in profiles)
)

# Strategy for generating keyword strings
keyword_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    min_size=1,
    max_size=30
).filter(lambda x: x.strip())

keywords_list_strategy = st.lists(keyword_strategy, min_size=1, max_size=10).map(
    lambda keywords: ", ".join(keywords)
)

# Strategy for generating non-negative integers
non_negative_int_strategy = st.integers(min_value=0, max_value=10000)

# Strategy for generating negative integers
negative_int_strategy = st.integers(min_value=-10000, max_value=-1)


# ─── Property 4: Campaign Name Validation Rejects Empty Names ────────────────


@given(name=empty_or_whitespace_strategy)
@settings(max_examples=20, deadline=None)  # Disable deadline due to import timing variability
def test_property_4_campaign_name_validation_rejects_empty_names(name):
    """
    **Validates: Requirements 3.1**
    
    Property 4: Campaign Name Validation Rejects Empty Names
    
    For any campaign creation request, if the campaign name is empty or 
    contains only whitespace, validation SHALL fail.
    """
    validator = get_validator()
    
    # Create a campaign with an empty/whitespace name
    # Use model_construct to bypass Pydantic validation and test the validator service
    campaign_data = CampaignCreateDTO.model_construct(
        name=name,
        search_type=SearchType.PROFILE,
        profiles="@testuser",
        min_likes=0,
        min_retweets=0,
        min_replies=0
    )
    
    # Validate the campaign
    result = validator.validate_create(campaign_data)
    
    # Validation should fail
    assert not result.is_valid, f"Validation should reject empty/whitespace name: '{name}'"
    assert "name" in result.errors, "Error should be associated with 'name' field"
    assert "empty" in result.errors["name"].lower(), "Error message should mention 'empty'"


# ─── Property 5: Profile Search Requires Profiles ────────────────────────────


@given(
    name=valid_name_strategy,
    profiles=empty_or_whitespace_strategy
)
@settings(max_examples=20)
def test_property_5_profile_search_requires_profiles(name, profiles):
    """
    **Validates: Requirements 3.2**
    
    Property 5: Profile Search Requires Profiles
    
    For any campaign creation request with search_type "profile", if no 
    profiles are provided or the profiles string is empty after parsing, 
    validation SHALL fail.
    """
    validator = get_validator()
    
    # Create a profile search campaign with empty profiles
    # Use model_construct to bypass Pydantic validation and test the validator service
    campaign_data = CampaignCreateDTO.model_construct(
        name=name,
        search_type=SearchType.PROFILE,
        profiles=profiles,
        min_likes=0,
        min_retweets=0,
        min_replies=0
    )
    
    # Validate the campaign
    result = validator.validate_create(campaign_data)
    
    # Validation should fail
    assert not result.is_valid, "Validation should reject profile search without profiles"
    assert "profiles" in result.errors, "Error should be associated with 'profiles' field"


# ─── Property 6: Keyword Search Requires Keywords ────────────────────────────


@given(
    name=valid_name_strategy,
    keywords=empty_or_whitespace_strategy
)
@settings(max_examples=20)
def test_property_6_keyword_search_requires_keywords(name, keywords):
    """
    **Validates: Requirements 3.3**
    
    Property 6: Keyword Search Requires Keywords
    
    For any campaign creation request with search_type "keywords", if no 
    keywords are provided or the keywords string is empty after parsing, 
    validation SHALL fail.
    """
    validator = get_validator()
    
    # Create a keyword search campaign with empty keywords
    # Use model_construct to bypass Pydantic validation and test the validator service
    campaign_data = CampaignCreateDTO.model_construct(
        name=name,
        search_type=SearchType.KEYWORDS,
        keywords=keywords,
        min_likes=0,
        min_retweets=0,
        min_replies=0
    )
    
    # Validate the campaign
    result = validator.validate_create(campaign_data)
    
    # Validation should fail
    assert not result.is_valid, "Validation should reject keyword search without keywords"
    assert "keywords" in result.errors, "Error should be associated with 'keywords' field"


# ─── Property 9: Engagement Filters Must Be Non-Negative ─────────────────────


@given(
    name=valid_name_strategy,
    profiles=profiles_list_strategy,
    min_likes=negative_int_strategy,
    min_retweets=negative_int_strategy,
    min_replies=negative_int_strategy
)
@settings(max_examples=20)
def test_property_9_engagement_filters_must_be_non_negative(
    name, profiles, min_likes, min_retweets, min_replies
):
    """
    **Validates: Requirements 3.6**
    
    Property 9: Engagement Filters Must Be Non-Negative
    
    For any campaign configuration, if any engagement filter (min_likes, 
    min_retweets, min_replies) is negative, validation SHALL fail.
    """
    validator = get_validator()
    
    # Test with negative min_likes
    # Use model_construct to bypass Pydantic validation and test the validator service
    campaign_data = CampaignCreateDTO.model_construct(
        name=name,
        search_type=SearchType.PROFILE,
        profiles=profiles,
        min_likes=min_likes,
        min_retweets=0,
        min_replies=0
    )
    
    result = validator.validate_create(campaign_data)
    assert not result.is_valid, "Validation should reject negative min_likes"
    assert "min_likes" in result.errors, "Error should be associated with 'min_likes' field"
    
    # Test with negative min_retweets
    campaign_data = CampaignCreateDTO.model_construct(
        name=name,
        search_type=SearchType.PROFILE,
        profiles=profiles,
        min_likes=0,
        min_retweets=min_retweets,
        min_replies=0
    )
    
    result = validator.validate_create(campaign_data)
    assert not result.is_valid, "Validation should reject negative min_retweets"
    assert "min_retweets" in result.errors, "Error should be associated with 'min_retweets' field"
    
    # Test with negative min_replies
    campaign_data = CampaignCreateDTO.model_construct(
        name=name,
        search_type=SearchType.PROFILE,
        profiles=profiles,
        min_likes=0,
        min_retweets=0,
        min_replies=min_replies
    )
    
    result = validator.validate_create(campaign_data)
    assert not result.is_valid, "Validation should reject negative min_replies"
    assert "min_replies" in result.errors, "Error should be associated with 'min_replies' field"


# ─── Additional Property: Valid Campaigns Pass Validation ────────────────────


@given(
    name=valid_name_strategy,
    profiles=profiles_list_strategy,
    min_likes=non_negative_int_strategy,
    min_retweets=non_negative_int_strategy,
    min_replies=non_negative_int_strategy
)
@settings(max_examples=10)
def test_valid_profile_campaigns_pass_validation(
    name, profiles, min_likes, min_retweets, min_replies
):
    """
    Additional property: Valid profile search campaigns should pass validation.
    
    This ensures that the validator doesn't reject valid inputs.
    """
    validator = get_validator()
    
    campaign_data = CampaignCreateDTO(
        name=name,
        search_type=SearchType.PROFILE,
        profiles=profiles,
        min_likes=min_likes,
        min_retweets=min_retweets,
        min_replies=min_replies
    )
    
    result = validator.validate_create(campaign_data)
    
    assert result.is_valid, f"Valid campaign should pass validation. Errors: {result.errors}"
    assert len(result.errors) == 0, "Valid campaign should have no errors"


@given(
    name=valid_name_strategy,
    keywords=keywords_list_strategy,
    min_likes=non_negative_int_strategy,
    min_retweets=non_negative_int_strategy,
    min_replies=non_negative_int_strategy
)
@settings(max_examples=10)
def test_valid_keyword_campaigns_pass_validation(
    name, keywords, min_likes, min_retweets, min_replies
):
    """
    Additional property: Valid keyword search campaigns should pass validation.
    
    This ensures that the validator doesn't reject valid inputs.
    """
    validator = get_validator()
    
    campaign_data = CampaignCreateDTO(
        name=name,
        search_type=SearchType.KEYWORDS,
        keywords=keywords,
        min_likes=min_likes,
        min_retweets=min_retweets,
        min_replies=min_replies
    )
    
    result = validator.validate_create(campaign_data)
    
    assert result.is_valid, f"Valid campaign should pass validation. Errors: {result.errors}"
    assert len(result.errors) == 0, "Valid campaign should have no errors"
