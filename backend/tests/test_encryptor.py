"""
Unit Tests for Encryptor

Tests the AES-256-GCM encryption and decryption functionality.
"""

import os
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

import base64
import pytest
from src.utils.encryption import Encryptor


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def encryptor():
    """Create an Encryptor with a test key"""
    key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    return Encryptor(key_b64=key)


# ─── Test encrypt ────────────────────────────────────────────────────────────


def test_encrypt_returns_different_value(encryptor):
    """Test that encrypt returns a value different from plaintext"""
    plaintext = "my_secret_token_12345"
    encrypted = encryptor.encrypt(plaintext)
    
    assert encrypted != plaintext


def test_encrypt_returns_base64_string(encryptor):
    """Test that encrypt returns a valid base64 string"""
    plaintext = "my_secret_token_12345"
    encrypted = encryptor.encrypt(plaintext)
    
    # Should be decodable as base64
    try:
        base64.urlsafe_b64decode(encrypted)
    except Exception:
        pytest.fail("Encrypted value is not valid base64")


def test_encrypt_produces_unique_ciphertexts(encryptor):
    """Test that encrypting the same plaintext twice produces different ciphertexts"""
    plaintext = "my_secret_token_12345"
    encrypted1 = encryptor.encrypt(plaintext)
    encrypted2 = encryptor.encrypt(plaintext)
    
    # Different ciphertexts due to unique IVs
    assert encrypted1 != encrypted2


def test_encrypt_handles_empty_string(encryptor):
    """Test that encrypt handles empty string"""
    plaintext = ""
    encrypted = encryptor.encrypt(plaintext)
    
    assert encrypted != ""
    assert isinstance(encrypted, str)


def test_encrypt_handles_long_strings(encryptor):
    """Test that encrypt handles long strings"""
    plaintext = "a" * 10000
    encrypted = encryptor.encrypt(plaintext)
    
    assert encrypted != plaintext
    assert len(encrypted) > 0


def test_encrypt_handles_special_characters(encryptor):
    """Test that encrypt handles special characters"""
    plaintext = "token!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
    encrypted = encryptor.encrypt(plaintext)
    
    assert encrypted != plaintext


def test_encrypt_handles_unicode(encryptor):
    """Test that encrypt handles unicode characters"""
    plaintext = "token_with_émojis_🔐🔑"
    encrypted = encryptor.encrypt(plaintext)
    
    assert encrypted != plaintext


# ─── Test decrypt ────────────────────────────────────────────────────────────


def test_decrypt_reverses_encrypt(encryptor):
    """Test that decrypt reverses encrypt"""
    plaintext = "my_secret_token_12345"
    encrypted = encryptor.encrypt(plaintext)
    decrypted = encryptor.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_decrypt_handles_empty_string(encryptor):
    """Test that decrypt handles encrypted empty string"""
    plaintext = ""
    encrypted = encryptor.encrypt(plaintext)
    decrypted = encryptor.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_decrypt_handles_long_strings(encryptor):
    """Test that decrypt handles long encrypted strings"""
    plaintext = "a" * 10000
    encrypted = encryptor.encrypt(plaintext)
    decrypted = encryptor.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_decrypt_handles_special_characters(encryptor):
    """Test that decrypt handles special characters"""
    plaintext = "token!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
    encrypted = encryptor.encrypt(plaintext)
    decrypted = encryptor.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_decrypt_handles_unicode(encryptor):
    """Test that decrypt handles unicode characters"""
    plaintext = "token_with_émojis_🔐🔑"
    encrypted = encryptor.encrypt(plaintext)
    decrypted = encryptor.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_decrypt_raises_error_on_invalid_base64(encryptor):
    """Test that decrypt raises error on invalid base64"""
    invalid_token = "not-valid-base64!!!"
    
    with pytest.raises(ValueError) as exc_info:
        encryptor.decrypt(invalid_token)
    
    # Could fail on base64 decoding or on length check
    error_msg = str(exc_info.value).lower()
    assert "base64" in error_msg or "too short" in error_msg


def test_decrypt_raises_error_on_too_short_token(encryptor):
    """Test that decrypt raises error on token that's too short"""
    # Create a valid base64 string that's too short
    short_token = base64.urlsafe_b64encode(b"short").decode()
    
    with pytest.raises(ValueError) as exc_info:
        encryptor.decrypt(short_token)
    
    assert "too short" in str(exc_info.value).lower()


def test_decrypt_raises_error_on_tampered_ciphertext(encryptor):
    """Test that decrypt raises error on tampered ciphertext"""
    plaintext = "my_secret_token_12345"
    encrypted = encryptor.encrypt(plaintext)
    
    # Tamper with the encrypted data
    encrypted_bytes = base64.urlsafe_b64decode(encrypted)
    tampered_bytes = encrypted_bytes[:-1] + b'X'  # Change last byte
    tampered_token = base64.urlsafe_b64encode(tampered_bytes).decode()
    
    with pytest.raises(ValueError) as exc_info:
        encryptor.decrypt(tampered_token)
    
    assert "decrypt" in str(exc_info.value).lower() or "tamper" in str(exc_info.value).lower()


def test_decrypt_with_different_encryptor_fails(encryptor):
    """Test that decrypt fails when using a different encryptor (different key)"""
    plaintext = "my_secret_token_12345"
    encrypted = encryptor.encrypt(plaintext)
    
    # Create a different encryptor with a different key
    different_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    different_encryptor = Encryptor(key_b64=different_key)
    
    with pytest.raises(ValueError):
        different_encryptor.decrypt(encrypted)


# ─── Test initialization ─────────────────────────────────────────────────────


def test_encryptor_initialization_with_valid_key():
    """Test that Encryptor initializes with a valid key"""
    key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    encryptor = Encryptor(key_b64=key)
    
    assert encryptor is not None


def test_encryptor_initialization_rejects_short_key():
    """Test that Encryptor rejects keys that are too short"""
    short_key = base64.urlsafe_b64encode(os.urandom(16)).decode()  # Only 16 bytes
    
    with pytest.raises(ValueError) as exc_info:
        Encryptor(key_b64=short_key)
    
    assert "32 bytes" in str(exc_info.value)


def test_encryptor_initialization_rejects_long_key():
    """Test that Encryptor rejects keys that are too long"""
    long_key = base64.urlsafe_b64encode(os.urandom(64)).decode()  # 64 bytes
    
    with pytest.raises(ValueError) as exc_info:
        Encryptor(key_b64=long_key)
    
    assert "32 bytes" in str(exc_info.value)


def test_encryptor_initialization_rejects_invalid_base64():
    """Test that Encryptor rejects invalid base64 keys"""
    invalid_key = "not-valid-base64!!!"
    
    with pytest.raises(Exception):  # Could be ValueError or binascii.Error
        Encryptor(key_b64=invalid_key)


# ─── Test round-trip with multiple values ────────────────────────────────────


def test_multiple_encrypt_decrypt_cycles(encryptor):
    """Test multiple encrypt/decrypt cycles with different values"""
    test_values = [
        "short",
        "medium_length_token_12345",
        "very_long_token_" * 100,
        "special!@#$%^&*()",
        "unicode_émojis_🔐",
        "",
    ]
    
    for plaintext in test_values:
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == plaintext, f"Failed for: {plaintext}"
