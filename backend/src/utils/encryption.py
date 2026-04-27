"""
AES-256-GCM encryption service for storing API tokens securely.

Each call to encrypt() generates a unique 96-bit IV (nonce), so the same
plaintext produces a different ciphertext every time — preventing replay
and pattern-analysis attacks.

Storage format (base64-encoded):
    <12-byte IV> | <ciphertext> | <16-byte GCM tag>
All three parts are concatenated before base64 encoding.
"""

import base64
import os
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger("utils.encryption")

_IV_LENGTH = 12   # 96 bits — recommended for GCM
_KEY_LENGTH = 32  # 256 bits


class Encryptor:
    """
    AES-256-GCM encryptor.

    The encryption key is loaded from the ENCRYPTION_KEY environment variable.
    The key must be a URL-safe base64-encoded 32-byte value.

    Generate a suitable key with:
        python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
    """

    def __init__(self, key_b64: Optional[str] = None) -> None:
        raw_key = base64.urlsafe_b64decode(key_b64 or settings.encryption_key)
        if len(raw_key) != _KEY_LENGTH:
            raise ValueError(
                f"Encryption key must be {_KEY_LENGTH} bytes "
                f"(got {len(raw_key)} bytes after base64 decoding)"
            )
        self._aesgcm = AESGCM(raw_key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt *plaintext* and return a base64-encoded string.

        A fresh random IV is generated for every call.
        """
        iv = os.urandom(_IV_LENGTH)
        ciphertext_with_tag = self._aesgcm.encrypt(iv, plaintext.encode(), None)
        # Prepend IV so we can recover it during decryption
        payload = iv + ciphertext_with_tag
        return base64.urlsafe_b64encode(payload).decode()

    def decrypt(self, token: str) -> str:
        """
        Decrypt a base64-encoded token produced by :meth:`encrypt`.

        Raises ``ValueError`` if the token is malformed or the authentication
        tag does not match (i.e. the ciphertext has been tampered with).
        """
        try:
            payload = base64.urlsafe_b64decode(token)
        except Exception as exc:
            raise ValueError("Invalid base64 encoding in encrypted token") from exc

        if len(payload) < _IV_LENGTH + 16:  # IV + minimum GCM tag
            raise ValueError("Encrypted token is too short to be valid")

        iv = payload[:_IV_LENGTH]
        ciphertext_with_tag = payload[_IV_LENGTH:]

        try:
            plaintext_bytes = self._aesgcm.decrypt(iv, ciphertext_with_tag, None)
        except Exception as exc:
            raise ValueError("Decryption failed — token may be corrupted or tampered") from exc

        return plaintext_bytes.decode()
