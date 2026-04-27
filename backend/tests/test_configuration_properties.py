"""
Property-Based Tests for Configuration Management

Tests the correctness properties defined in design.md using Hypothesis.
These tests verify that configuration operations maintain their invariants
across a wide range of inputs.
"""

import base64
import os
from unittest.mock import Mock
from hypothesis import given, strategies as st, settings
import pytest

# Import after conftest sets up environment
from src.models.configuration import ConfigurationDTO, ConfigurationResponseDTO
from src.repositories.configuration_repository import ConfigurationRepository


# ─── Helper Functions ────────────────────────────────────────────────────────


def create_encryptor():
    """Create an Encryptor instance with a test key"""
    from src.utils.encryption import Encryptor
    key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    return Encryptor(key_b64=key)


def create_config_manager(encryptor=None):
    """Create a ConfigurationManager with mocked dependencies"""
    from src.services.configuration_manager import ConfigurationManager
    if encryptor is None:
        encryptor = create_encryptor()
    mock_repo = Mock(spec=ConfigurationRepository)
    return ConfigurationManager(repo=mock_repo, encryptor=encryptor)


def get_mask_function():
    """Get the _mask function"""
    from src.services.configuration_manager import _mask
    return _mask


# ─── Hypothesis Strategies ───────────────────────────────────────────────────


# Strategy for generating valid email addresses
emails_strategy = st.emails()

# Strategy for generating API tokens (alphanumeric strings with underscores)
token_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
    min_size=10,
    max_size=100
)

# Strategy for generating passwords
password_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "P")),
    min_size=8,
    max_size=50
)

# Strategy for generating complete valid configurations
configuration_strategy = st.builds(
    ConfigurationDTO,
    user_email=emails_strategy,
    apify_token=token_strategy,
    openai_token=token_strategy,
    smtp_password=password_strategy,
    twitter_auth_token=st.one_of(st.none(), token_strategy),
    twitter_ct0=st.one_of(st.none(), token_strategy)
)


# ─── Property 1: Configuration Round-Trip Preserves Data ─────────────────────


@given(config=configuration_strategy)
@settings(max_examples=20, deadline=500)  # Increased deadline for encryption operations
def test_property_1_configuration_round_trip(config):
    """
    **Validates: Requirements 1.3, 1.5, 1.7**
    
    Property 1: Configuration Round-Trip Preserves Data
    
    For any valid configuration with email and API tokens, storing the 
    configuration in the database and then retrieving it SHALL produce a 
    configuration with equivalent values (tokens may be encrypted in storage 
    but must decrypt to original values).
    """
    # Import here to avoid loading settings at module level
    from src.services.configuration_manager import ConfigurationManager
    
    # Create encryptor for this test
    encryptor = create_encryptor()
    
    # Create a mock repository that simulates database storage
    mock_repo = Mock(spec=ConfigurationRepository)
    stored_data = {}
    
    def mock_create(record):
        stored_data.clear()
        stored_data.update(record)
        stored_data["id"] = "test-id-123"
        return stored_data
    
    def mock_update(record_id, updates):
        stored_data.update(updates)
        return stored_data
    
    def mock_get():
        return stored_data if stored_data else None
    
    mock_repo.create = Mock(side_effect=mock_create)
    mock_repo.update = Mock(side_effect=mock_update)
    mock_repo.get = Mock(side_effect=mock_get)
    
    # Create manager with mocked repository
    manager = ConfigurationManager(repo=mock_repo, encryptor=encryptor)
    
    # Save configuration
    manager.save_configuration(config)
    
    # Retrieve configuration
    retrieved = manager.get_configuration()
    
    # Assert all fields match
    assert retrieved.user_email == config.user_email
    assert retrieved.apify_token == config.apify_token
    assert retrieved.openai_token == config.openai_token
    assert retrieved.smtp_password == config.smtp_password
    assert retrieved.twitter_auth_token == config.twitter_auth_token
    assert retrieved.twitter_ct0 == config.twitter_ct0


# ─── Property 2: Token Masking Never Exposes Complete Tokens ────────────────


@given(token=token_strategy)
@settings(max_examples=20)
def test_property_2_token_masking_never_exposes_complete_tokens(token):
    """
    **Validates: Requirements 1.4, 16.3, 16.4**
    
    Property 2: Token Masking Never Exposes Complete Tokens
    
    For any API token string, the masking function SHALL return a string that 
    is different from the input and follows the pattern of showing only first 
    and last few characters (e.g., "apify_XXX...XXX").
    """
    mask_function = get_mask_function()
    masked = mask_function(token)
    
    # Masked token must be different from original
    assert masked != token
    
    # Masked token should not contain the full original token
    # (except for very short tokens which become "***")
    if len(token) > 8:
        # For longer tokens, the middle section should be hidden
        assert "..." in masked
        # The masked version should start with the first few chars
        assert masked.startswith(token[:4])
        # The masked version should end with the last few chars
        assert masked.endswith(token[-4:])
        # The complete token should not be present in the masked version
        assert token not in masked
    else:
        # Very short tokens should be completely masked
        assert masked == "***"


# ─── Property 3: Configuration Validation Rejects Incomplete Data ────────────


@given(
    email=emails_strategy,
    apify_token=st.one_of(st.just(""), st.just("   "), token_strategy),
    openai_token=st.one_of(st.just(""), st.just("   "), token_strategy),
    smtp_password=st.one_of(st.just(""), st.just("   "), password_strategy)
)
@settings(max_examples=20)
def test_property_3_configuration_validation_rejects_incomplete_data(
    email, apify_token, openai_token, smtp_password
):
    """
    **Validates: Requirements 1.2**
    
    Property 3: Configuration Validation Rejects Incomplete Data
    
    For any configuration object, if any required field (email, apify_token, 
    openai_token, smtp_password) is missing or empty, validation SHALL fail 
    with a descriptive error message.
    """
    config_manager = create_config_manager()
    
    config = ConfigurationDTO(
        user_email=email,
        apify_token=apify_token,
        openai_token=openai_token,
        smtp_password=smtp_password
    )
    
    is_valid = config_manager.validate_tokens(config)
    
    # Check if any required field is empty or whitespace-only
    has_empty_field = (
        not apify_token.strip() or
        not openai_token.strip() or
        not smtp_password.strip()
    )
    
    # Validation should fail if any field is empty
    if has_empty_field:
        assert not is_valid, "Validation should reject configuration with empty fields"
    else:
        assert is_valid, "Validation should accept configuration with all fields filled"


# ─── Property 22: Token Encryption Is Reversible ─────────────────────────────


@given(token=token_strategy)
@settings(max_examples=20)
def test_property_22_token_encryption_is_reversible(token):
    """
    **Validates: Requirements 16.1**
    
    Property 22: Token Encryption Is Reversible
    
    For any API token, encrypting the token and then decrypting it SHALL 
    produce the original token value.
    """
    encryptor = create_encryptor()
    
    # Encrypt the token
    encrypted = encryptor.encrypt(token)
    
    # Encrypted value should be different from original
    assert encrypted != token
    
    # Decrypt the token
    decrypted = encryptor.decrypt(encrypted)
    
    # Decrypted value should match original exactly
    assert decrypted == token


# ─── Additional Property: Multiple Encryptions Produce Different Ciphertexts ─


@given(token=token_strategy)
@settings(max_examples=10)
def test_encryption_produces_unique_ciphertexts(token):
    """
    Additional security property: Multiple encryptions of the same plaintext
    should produce different ciphertexts (due to unique IVs).
    
    This prevents pattern analysis attacks.
    """
    encryptor = create_encryptor()
    
    encrypted1 = encryptor.encrypt(token)
    encrypted2 = encryptor.encrypt(token)
    
    # Different ciphertexts
    assert encrypted1 != encrypted2
    
    # But both decrypt to the same plaintext
    assert encryptor.decrypt(encrypted1) == token
    assert encryptor.decrypt(encrypted2) == token


# ─── Additional Property: Masking Preserves Token Boundaries ────────────────


@given(config=configuration_strategy)
@settings(max_examples=10)
def test_mask_tokens_preserves_structure(config):
    """
    Additional property: The mask_tokens method should preserve the structure
    of the configuration and correctly indicate presence of optional tokens.
    """
    config_manager = create_config_manager()
    masked_response = config_manager.mask_tokens(config)
    
    # Response should be a ConfigurationResponseDTO
    assert isinstance(masked_response, ConfigurationResponseDTO)
    
    # Email should be preserved (not masked)
    assert masked_response.user_email == config.user_email
    
    # All required tokens should be masked (not equal to originals)
    assert masked_response.apify_token_masked != config.apify_token
    assert masked_response.openai_token_masked != config.openai_token
    assert masked_response.smtp_password_masked == "***"
    
    # Optional token presence should be correctly indicated
    assert masked_response.twitter_auth_token_present == bool(config.twitter_auth_token)
    assert masked_response.twitter_ct0_present == bool(config.twitter_ct0)
