"""
Storage Service — manages file uploads/downloads via Supabase Storage.

Organizes campaign documents in a structured folder hierarchy:
    campaign-documents/campaigns/{campaign_id}/results.docx
"""

from __future__ import annotations

import os
from supabase import Client

from src.core.logging_config import get_logger

logger = get_logger("services.storage_service")

_BUCKET = "campaign-documents"


class StorageService:
    """Manages campaign document storage in Supabase Storage."""

    def __init__(self, supabase_client: Client) -> None:
        self._client = supabase_client

    # ─── Upload ──────────────────────────────────────────────────────────────

    def upload_document(self, campaign_id: str, file_path: str) -> str:
        """
        Upload a .docx file to Supabase Storage.

        Returns the public URL of the uploaded file.
        Raises RuntimeError on upload failure.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Storage path: campaigns/{campaign_id}/results.docx
        storage_path = f"campaigns/{campaign_id}/results.docx"

        try:
            with open(file_path, "rb") as f:
                self._client.storage.from_(_BUCKET).upload(
                    path=storage_path,
                    file=f,
                    file_options={
                        "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    },
                )
            logger.info("Uploaded document to %s/%s", _BUCKET, storage_path)
        except Exception as exc:
            logger.error("Failed to upload document: %s", exc)
            raise RuntimeError(f"Storage upload failed: {exc}") from exc

        # Return the public URL (or signed URL if bucket is private)
        public_url = self._client.storage.from_(_BUCKET).get_public_url(storage_path)
        return public_url

    # ─── Download / Signed URLs ──────────────────────────────────────────────

    def get_signed_url(self, campaign_id: str, expires_in: int = 3600) -> str:
        """
        Generate a temporary signed URL for downloading a campaign document.

        *expires_in*: URL validity in seconds (default 1 hour).
        Raises RuntimeError if the file does not exist or signing fails.
        """
        storage_path = f"campaigns/{campaign_id}/results.docx"
        try:
            response = self._client.storage.from_(_BUCKET).create_signed_url(
                path=storage_path,
                expires_in=expires_in,
            )
            signed_url = response.get("signedURL") or response.get("signedUrl")
            if not signed_url:
                raise RuntimeError("Supabase did not return a signed URL")
            logger.info("Generated signed URL for %s (expires in %ds)", storage_path, expires_in)
            return signed_url
        except Exception as exc:
            logger.error("Failed to generate signed URL: %s", exc)
            raise RuntimeError(f"Failed to generate signed URL: {exc}") from exc

    # ─── Delete ──────────────────────────────────────────────────────────────

    def delete_document(self, campaign_id: str) -> None:
        """
        Delete a campaign document from storage.

        Does not raise an error if the file does not exist.
        """
        storage_path = f"campaigns/{campaign_id}/results.docx"
        try:
            self._client.storage.from_(_BUCKET).remove([storage_path])
            logger.info("Deleted document: %s", storage_path)
        except Exception as exc:
            logger.warning("Failed to delete document %s: %s", storage_path, exc)
