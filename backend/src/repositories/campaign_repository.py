"""
Campaign Repository — CRUD operations for campaigns, results, and analysis.
"""

from typing import Optional, List
from supabase import Client

from src.core.logging_config import get_logger

logger = get_logger("repositories.campaign")

_CAMPAIGNS = "campaigns"
_RESULTS = "campaign_results"
_ANALYSIS = "campaign_analysis"


class CampaignRepository:
    """Data-access layer for campaign-related tables."""

    def __init__(self, db: Client) -> None:
        self._db = db

    # ─── Campaigns ───────────────────────────────────────────────────────────

    def create(self, record: dict) -> dict:
        """Insert a new campaign record. Returns the inserted row."""
        response = self._db.table(_CAMPAIGNS).insert(record).execute()
        logger.info("Campaign created: %s", response.data[0].get("id"))
        return response.data[0]

    def get_by_id(self, campaign_id: str) -> Optional[dict]:
        """Retrieve a campaign by its UUID. Returns ``None`` if not found."""
        response = self._db.table(_CAMPAIGNS).select("*").eq("id", campaign_id).limit(1).execute()
        # Return None if no data or empty list
        if not response.data or len(response.data) == 0:
            return None
        return response.data[0]

    def list_all(self, limit: int = 20, offset: int = 0) -> List[dict]:
        """
        List campaigns ordered by creation date (newest first).

        Returns a page of *limit* records starting at *offset*.
        """
        response = (
            self._db.table(_CAMPAIGNS)
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return response.data or []

    def count_all(self) -> int:
        """Return the total number of campaign records."""
        response = self._db.table(_CAMPAIGNS).select("id", count="exact").execute()
        return response.count or 0

    def update_status(
        self,
        campaign_id: str,
        status: str,
        *,
        error_message: Optional[str] = None,
        document_url: Optional[str] = None,
        results_count: Optional[int] = None,
    ) -> None:
        """Update the status (and optional fields) of a campaign."""
        updates: dict = {"status": status}
        if error_message is not None:
            updates["error_message"] = error_message
        if document_url is not None:
            updates["document_url"] = document_url
        if results_count is not None:
            updates["results_count"] = results_count
        if status == "completed":
            # Let the DB set completed_at via NOW() by passing a raw expression
            updates["completed_at"] = "now()"

        self._db.table(_CAMPAIGNS).update(updates).eq("id", campaign_id).execute()
        logger.info("Campaign %s status → %s", campaign_id, status)

    def delete(self, campaign_id: str) -> None:
        """
        Delete a campaign and all its associated data.

        The database CASCADE will automatically delete:
        - campaign_results
        - campaign_analysis
        """
        self._db.table(_CAMPAIGNS).delete().eq("id", campaign_id).execute()
        logger.info("Deleted campaign: %s", campaign_id)

    # ─── Results ─────────────────────────────────────────────────────────────

    def save_results(self, campaign_id: str, tweets: List[dict]) -> None:
        """
        Bulk-insert tweet results for a campaign.

        Each dict in *tweets* must match the ``campaign_results`` schema.
        """
        if not tweets:
            return
        records = [{"campaign_id": campaign_id, **t} for t in tweets]
        self._db.table(_RESULTS).insert(records).execute()
        logger.info("Saved %d tweet results for campaign %s", len(tweets), campaign_id)

    def get_results(self, campaign_id: str) -> List[dict]:
        """Retrieve all tweet results for a campaign, ordered by timestamp."""
        response = (
            self._db.table(_RESULTS)
            .select("*")
            .eq("campaign_id", campaign_id)
            .order("timestamp", desc=True)
            .execute()
        )
        return response.data or []

    # ─── Analysis ────────────────────────────────────────────────────────────

    def save_analysis(self, campaign_id: str, analysis_text: str) -> None:
        """Insert an analysis record for a campaign."""
        self._db.table(_ANALYSIS).insert(
            {"campaign_id": campaign_id, "analysis_text": analysis_text}
        ).execute()
        logger.info("Analysis saved for campaign %s", campaign_id)

    def get_analysis(self, campaign_id: str) -> Optional[dict]:
        """Retrieve the analysis record for a campaign."""
        response = (
            self._db.table(_ANALYSIS).select("*").eq("campaign_id", campaign_id).limit(1).execute()
        )
        return response.data[0] if response.data else None

    def delete_results(self, campaign_id: str) -> None:
        """Delete all tweet results for a campaign."""
        self._db.table(_RESULTS).delete().eq("campaign_id", campaign_id).execute()
        logger.info("Deleted results for campaign %s", campaign_id)

    def delete_analysis(self, campaign_id: str) -> None:
        """Delete all analysis records (legacy) for a campaign."""
        self._db.table(_ANALYSIS).delete().eq("campaign_id", campaign_id).execute()
        logger.info("Deleted analysis for campaign %s", campaign_id)
