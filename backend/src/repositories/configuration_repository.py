"""
Configuration Repository — CRUD operations for the `configurations` table.

All token values stored here are already encrypted by ConfigurationManager
before being passed to this repository.
"""

from typing import Optional
from supabase import Client

from src.core.logging_config import get_logger

logger = get_logger("repositories.configuration")

_TABLE = "configurations"


class ConfigurationRepository:
    """Data-access layer for user configuration records."""

    def __init__(self, db: Client) -> None:
        self._db = db

    # ─── Write ───────────────────────────────────────────────────────────────

    def create(self, record: dict) -> dict:
        """
        Insert a new configuration record.

        *record* must contain all required encrypted fields.
        Returns the inserted row.
        """
        response = self._db.table(_TABLE).insert(record).execute()
        logger.info("Configuration record created")
        return response.data[0]

    def update(self, record_id: str, updates: dict) -> dict:
        """
        Update an existing configuration record by primary key.

        Returns the updated row.
        """
        response = self._db.table(_TABLE).update(updates).eq("id", record_id).execute()
        logger.info("Configuration record %s updated", record_id)
        return response.data[0]

    # ─── Read ────────────────────────────────────────────────────────────────

    def get(self) -> Optional[dict]:
        """
        Retrieve the single configuration record (MVP: single-user).

        Returns ``None`` if no configuration has been saved yet.
        """
        response = self._db.table(_TABLE).select("*").limit(1).execute()
        if response.data:
            return response.data[0]
        return None

    def get_by_email(self, email: str) -> Optional[dict]:
        """
        Retrieve a configuration record by user email.

        Returns ``None`` if not found.
        """
        response = self._db.table(_TABLE).select("*").eq("user_email", email).limit(1).execute()
        if response.data:
            return response.data[0]
        return None

    # ─── Existence check ─────────────────────────────────────────────────────

    def exists(self) -> bool:
        """Return ``True`` if at least one configuration record exists."""
        response = self._db.table(_TABLE).select("id").limit(1).execute()
        return bool(response.data)
