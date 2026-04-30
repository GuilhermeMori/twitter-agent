"""
Unit Tests for ConfigurationManager

Tests the configuration management service with specific test cases
for save, get, mask, and validate operations.
"""

import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

import base64
from unittest.mock import Mock
import pytest

from src.models.configuration import ConfigurationDTO, ConfigurationResponseDTO
from src.repositories.configuration_repository import ConfigurationRepository
from src.services.configuration_manager import ConfigurationManager, _mask
from src.utils.encryption import Encryptor
from fastapi import HTTPException


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def encryptor():
    """Create an Encryptor with a test key"""
    key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    return Encryptor(key_b64=key)


@pytest.fixture
def mock_repo():
    """Create a mock ConfigurationRepository"""
    return Mock(spec=ConfigurationRepository)


@pytest.fixture
def config_manager(mock_repo, encryptor):
    """Create a ConfigurationManager with mocked dependencies"""
    return ConfigurationManager(repo=mock_repo, encryptor=encryptor)


@pytest.fixture
def sample_config():
    """Create a sample configuration"""
    return ConfigurationDTO(
        user_email="test@example.com",
        apify_token="apify_test_token_12345",
        openai_token="sk-test-openai-token-67890",
        smtp_password="smtp_password_123",
        twitter_auth_token="twitter_auth_abc123",
        twitter_ct0="ct0_token_xyz789",
    )


# ─── Test save_configuration ─────────────────────────────────────────────────


def test_save_configuration_creates_new_record(config_manager, mock_repo, sample_config):
    """Test that save_configuration creates a new record when none exists"""
    mock_repo.get.return_value = None
    mock_repo.create.return_value = {"id": "new-id"}

    config_manager.save_configuration(sample_config)

    mock_repo.get.assert_called_once()
    mock_repo.create.assert_called_once()

    # Verify encrypted data was passed to create
    call_args = mock_repo.create.call_args[0][0]
    assert call_args["user_email"] == sample_config.user_email
    assert "apify_token_encrypted" in call_args
    assert "openai_token_encrypted" in call_args
    assert "smtp_password_encrypted" in call_args


def test_save_configuration_updates_existing_record(config_manager, mock_repo, sample_config):
    """Test that save_configuration updates an existing record"""
    existing_record = {"id": "existing-id", "user_email": "old@example.com"}
    mock_repo.get.return_value = existing_record
    mock_repo.update.return_value = existing_record

    config_manager.save_configuration(sample_config)

    mock_repo.get.assert_called_once()
    # Verify update was called with the existing ID and some encrypted data
    assert mock_repo.update.call_count == 1
    call_args = mock_repo.update.call_args
    assert call_args[0][0] == "existing-id"
    assert "apify_token_encrypted" in call_args[0][1]
    mock_repo.create.assert_not_called()


def test_save_configuration_encrypts_all_tokens(
    config_manager, mock_repo, encryptor, sample_config
):
    """Test that all tokens are encrypted before storage"""
    mock_repo.get.return_value = None
    mock_repo.create.return_value = {"id": "new-id"}

    config_manager.save_configuration(sample_config)

    call_args = mock_repo.create.call_args[0][0]

    # Verify tokens are encrypted (different from plaintext)
    assert call_args["apify_token_encrypted"] != sample_config.apify_token
    assert call_args["openai_token_encrypted"] != sample_config.openai_token
    assert call_args["smtp_password_encrypted"] != sample_config.smtp_password

    # Verify they can be decrypted back to original
    assert encryptor.decrypt(call_args["apify_token_encrypted"]) == sample_config.apify_token
    assert encryptor.decrypt(call_args["openai_token_encrypted"]) == sample_config.openai_token
    assert encryptor.decrypt(call_args["smtp_password_encrypted"]) == sample_config.smtp_password


def test_save_configuration_handles_optional_twitter_tokens(config_manager, mock_repo):
    """Test that optional Twitter tokens are handled correctly"""
    config_without_twitter = ConfigurationDTO(
        user_email="test@example.com",
        apify_token="apify_token",
        openai_token="openai_token",
        smtp_password="smtp_pass",
        twitter_auth_token=None,
        twitter_ct0=None,
    )

    mock_repo.get.return_value = None
    mock_repo.create.return_value = {"id": "new-id"}

    config_manager.save_configuration(config_without_twitter)

    call_args = mock_repo.create.call_args[0][0]
    assert "twitter_auth_token_encrypted" not in call_args
    assert "twitter_ct0_encrypted" not in call_args


# ─── Test get_configuration ──────────────────────────────────────────────────


def test_get_configuration_returns_decrypted_config(
    config_manager, mock_repo, encryptor, sample_config
):
    """Test that get_configuration returns decrypted configuration"""
    encrypted_record = {
        "id": "test-id",
        "user_email": sample_config.user_email,
        "apify_token_encrypted": encryptor.encrypt(sample_config.apify_token),
        "openai_token_encrypted": encryptor.encrypt(sample_config.openai_token),
        "smtp_password_encrypted": encryptor.encrypt(sample_config.smtp_password),
        "twitter_auth_token_encrypted": encryptor.encrypt(sample_config.twitter_auth_token),
        "twitter_ct0_encrypted": encryptor.encrypt(sample_config.twitter_ct0),
    }
    mock_repo.get.return_value = encrypted_record

    result = config_manager.get_configuration()

    assert result.user_email == sample_config.user_email
    assert result.apify_token == sample_config.apify_token
    assert result.openai_token == sample_config.openai_token
    assert result.smtp_password == sample_config.smtp_password
    assert result.twitter_auth_token == sample_config.twitter_auth_token
    assert result.twitter_ct0 == sample_config.twitter_ct0


def test_get_configuration_raises_error_when_not_found(config_manager, mock_repo):
    """Test that get_configuration raises HTTPException when no config exists"""
    mock_repo.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        config_manager.get_configuration()

    assert exc_info.value.status_code == 400
    assert "not found" in exc_info.value.detail.lower()


def test_get_configuration_handles_missing_optional_tokens(config_manager, mock_repo, encryptor):
    """Test that get_configuration handles missing optional Twitter tokens"""
    encrypted_record = {
        "id": "test-id",
        "user_email": "test@example.com",
        "apify_token_encrypted": encryptor.encrypt("apify_token"),
        "openai_token_encrypted": encryptor.encrypt("openai_token"),
        "smtp_password_encrypted": encryptor.encrypt("smtp_pass"),
    }
    mock_repo.get.return_value = encrypted_record

    result = config_manager.get_configuration()

    assert result.twitter_auth_token is None
    assert result.twitter_ct0 is None


# ─── Test mask_tokens ────────────────────────────────────────────────────────


def test_mask_tokens_returns_masked_response(config_manager, sample_config):
    """Test that mask_tokens returns properly masked tokens"""
    result = config_manager.mask_tokens(sample_config)

    assert isinstance(result, ConfigurationResponseDTO)
    assert result.user_email == sample_config.user_email
    assert result.apify_token_masked != sample_config.apify_token
    assert result.openai_token_masked != sample_config.openai_token
    assert result.smtp_password_masked == "***"
    assert result.twitter_auth_token_present is True
    assert result.twitter_ct0_present is True


def test_mask_tokens_indicates_missing_optional_tokens(config_manager):
    """Test that mask_tokens correctly indicates missing optional tokens"""
    config = ConfigurationDTO(
        user_email="test@example.com",
        apify_token="apify_token",
        openai_token="openai_token",
        smtp_password="smtp_pass",
        twitter_auth_token=None,
        twitter_ct0=None,
    )

    result = config_manager.mask_tokens(config)

    assert result.twitter_auth_token_present is False
    assert result.twitter_ct0_present is False


# ─── Test validate_tokens ────────────────────────────────────────────────────


def test_validate_tokens_accepts_valid_config(config_manager, sample_config):
    """Test that validate_tokens accepts a valid configuration"""
    result = config_manager.validate_tokens(sample_config)
    assert result is True


def test_validate_tokens_rejects_empty_apify_token(config_manager):
    """Test that validate_tokens rejects empty apify_token"""
    config = ConfigurationDTO(
        user_email="test@example.com",
        apify_token="",
        openai_token="openai_token",
        smtp_password="smtp_pass",
    )

    result = config_manager.validate_tokens(config)
    assert result is False


def test_validate_tokens_rejects_whitespace_only_tokens(config_manager):
    """Test that validate_tokens rejects whitespace-only tokens"""
    config = ConfigurationDTO(
        user_email="test@example.com",
        apify_token="   ",
        openai_token="openai_token",
        smtp_password="smtp_pass",
    )

    result = config_manager.validate_tokens(config)
    assert result is False


def test_validate_tokens_rejects_empty_openai_token(config_manager):
    """Test that validate_tokens rejects empty openai_token"""
    config = ConfigurationDTO(
        user_email="test@example.com",
        apify_token="apify_token",
        openai_token="",
        smtp_password="smtp_pass",
    )

    result = config_manager.validate_tokens(config)
    assert result is False


def test_validate_tokens_rejects_empty_smtp_password(config_manager):
    """Test that validate_tokens rejects empty smtp_password"""
    config = ConfigurationDTO(
        user_email="test@example.com",
        apify_token="apify_token",
        openai_token="openai_token",
        smtp_password="",
    )

    result = config_manager.validate_tokens(config)
    assert result is False


# ─── Test configuration_exists ───────────────────────────────────────────────


def test_configuration_exists_returns_true_when_exists(config_manager, mock_repo):
    """Test that configuration_exists returns True when config exists"""
    mock_repo.exists.return_value = True

    result = config_manager.configuration_exists()
    assert result is True


def test_configuration_exists_returns_false_when_not_exists(config_manager, mock_repo):
    """Test that configuration_exists returns False when config doesn't exist"""
    mock_repo.exists.return_value = False

    result = config_manager.configuration_exists()
    assert result is False


# ─── Test _mask helper function ──────────────────────────────────────────────


def test_mask_function_masks_long_tokens():
    """Test that _mask function properly masks long tokens"""
    token = "apify_test_token_1234567890"
    masked = _mask(token)

    assert masked != token
    assert "..." in masked
    assert masked.startswith(token[:4])
    assert masked.endswith(token[-4:])


def test_mask_function_masks_short_tokens():
    """Test that _mask function completely masks short tokens"""
    token = "short"
    masked = _mask(token)

    assert masked == "***"


def test_mask_function_handles_medium_tokens():
    """Test that _mask function handles medium-length tokens"""
    token = "medium12"  # 8 characters
    masked = _mask(token)

    assert masked == "***"
