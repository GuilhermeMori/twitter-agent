"""
Configuration Manager — saves, retrieves, and masks user credentials.

Tokens are encrypted with AES-256-GCM before being stored in Supabase,
and decrypted on retrieval. The API layer only ever receives masked versions.
"""

from typing import Optional
from fastapi import HTTPException, status

from src.models.configuration import ConfigurationDTO, ConfigurationResponseDTO
from src.repositories.configuration_repository import ConfigurationRepository
from src.utils.encryption import Encryptor
from src.core.logging_config import get_logger

logger = get_logger("services.configuration_manager")

_MASK_VISIBLE = 4  # characters shown at each end of a masked token


def _mask(token: str) -> str:
    """Return a masked version of *token* showing only the first/last chars."""
    if len(token) <= _MASK_VISIBLE * 2:
        return "***"
    return f"{token[:_MASK_VISIBLE]}...{token[-_MASK_VISIBLE:]}"


class ConfigurationManager:
    """Manages user credentials with encryption and masking."""

    def __init__(
        self,
        repo: ConfigurationRepository,
        encryptor: Encryptor,
    ) -> None:
        self._repo = repo
        self._enc = encryptor

    # ─── Save ────────────────────────────────────────────────────────────────

    def save_configuration(self, config: ConfigurationDTO) -> None:
        """
        Encrypt all tokens and persist the configuration.

        If a record already exists it is updated; otherwise a new one is created.
        """
        encrypted: dict = {
            "user_email": config.user_email,
            "apify_token_encrypted": self._enc.encrypt(config.apify_token),
            "openai_token_encrypted": self._enc.encrypt(config.openai_token),
            "smtp_password_encrypted": self._enc.encrypt(config.smtp_password),
        }
        if config.twitter_auth_token:
            encrypted["twitter_auth_token_encrypted"] = self._enc.encrypt(
                config.twitter_auth_token
            )
        if config.twitter_ct0:
            encrypted["twitter_ct0_encrypted"] = self._enc.encrypt(config.twitter_ct0)

        existing = self._repo.get()
        if existing:
            self._repo.update(existing["id"], encrypted)
            logger.info("Configuration updated for %s", config.user_email)
        else:
            self._repo.create(encrypted)
            logger.info("Configuration created for %s", config.user_email)

    # ─── Retrieve ────────────────────────────────────────────────────────────

    def get_configuration(self) -> ConfigurationDTO:
        """
        Retrieve and decrypt the stored configuration.

        Raises HTTP 400 if no configuration has been saved yet.
        """
        record = self._repo.get()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configuration not found. Please configure API tokens first.",
            )

        return ConfigurationDTO(
            user_email=record["user_email"],
            apify_token=self._enc.decrypt(record["apify_token_encrypted"]),
            openai_token=self._enc.decrypt(record["openai_token_encrypted"]),
            smtp_password=self._enc.decrypt(record["smtp_password_encrypted"]),
            twitter_auth_token=(
                self._enc.decrypt(record["twitter_auth_token_encrypted"])
                if record.get("twitter_auth_token_encrypted")
                else None
            ),
            twitter_ct0=(
                self._enc.decrypt(record["twitter_ct0_encrypted"])
                if record.get("twitter_ct0_encrypted")
                else None
            ),
        )

    # ─── Mask ────────────────────────────────────────────────────────────────

    def mask_tokens(self, config: ConfigurationDTO) -> ConfigurationResponseDTO:
        """
        Return a response-safe version of the configuration with masked tokens.

        Never exposes complete token values (Property 2 from design.md).
        """
        return ConfigurationResponseDTO(
            user_email=config.user_email,
            apify_token_masked=_mask(config.apify_token),
            openai_token_masked=_mask(config.openai_token),
            smtp_password_masked="***",
            twitter_auth_token_present=bool(config.twitter_auth_token),
            twitter_ct0_present=bool(config.twitter_ct0),
        )

    # ─── Existence check ─────────────────────────────────────────────────────

    def configuration_exists(self) -> bool:
        """Return ``True`` if a configuration record exists in the database."""
        return self._repo.exists()
