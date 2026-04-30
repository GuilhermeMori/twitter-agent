"""
Campaign Service — orchestrates campaign creation and retrieval.

Ties together validation, parsing, persistence, and task enqueueing.
"""

import math
from typing import List, Optional

from fastapi import HTTPException, status

from src.models.campaign import (
    Campaign,
    CampaignConfig,
    CampaignCreateDTO,
    CampaignStatus,
    PaginatedResponse,
    SearchType,
    Tweet,
)
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.tweet_analysis_repository import TweetAnalysisRepository
from src.repositories.tweet_comment_repository import TweetCommentRepository
from src.services.campaign_parser import CampaignParser
from src.services.campaign_validator import CampaignValidator
from src.core.logging_config import get_logger

logger = get_logger("services.campaign_service")


class CampaignService:
    """Business logic for campaign management."""

    def __init__(
        self,
        repo: CampaignRepository,
        validator: CampaignValidator,
        analysis_repo: Optional[TweetAnalysisRepository] = None,
        comment_repo: Optional[TweetCommentRepository] = None,
    ) -> None:
        self._repo = repo
        self._validator = validator
        self._analysis_repo = analysis_repo
        self._comment_repo = comment_repo

    # ─── Create ──────────────────────────────────────────────────────────────

    def create_campaign(self, data: CampaignCreateDTO) -> str:
        """
        Validate, parse, persist, and enqueue a new campaign.

        Returns the new campaign's UUID string.
        Raises HTTP 400 on validation failure.
        """
        # 1. Validate
        result = self._validator.validate_create(data)
        if not result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Validation failed", "errors": result.errors},
            )

        # 2. Parse profiles / keywords
        profiles: List[str] | None = None
        keywords: List[str] | None = None

        if data.search_type == SearchType.PROFILE and data.profiles:
            profiles = CampaignParser.parse_profiles(data.profiles)
        elif data.search_type == SearchType.KEYWORDS and data.keywords:
            keywords = CampaignParser.parse_keywords(data.keywords)

        # 3. Build config JSONB
        config = CampaignConfig(
            profiles=profiles,
            keywords=keywords,
            language=data.language,
            min_likes=data.min_likes,
            min_retweets=data.min_retweets,
            min_replies=data.min_replies,
            days_back=data.days_back,
            max_tweets=data.max_tweets,
        )

        # 4. Persist
        record = {
            "name": data.name,
            "social_network": data.social_network,
            "search_type": data.search_type.value,
            "config": config.model_dump(),
            "status": CampaignStatus.PENDING.value,
            "communication_style_id": data.communication_style_id,
        }
        created = self._repo.create(record)
        campaign_id: str = created["id"]
        logger.info("Campaign %s created (status=pending)", campaign_id)

        # 5. Enqueue — imported here to avoid circular imports at module load
        from src.workers.campaign_executor import execute_campaign  # noqa: PLC0415

        execute_campaign.delay(campaign_id)
        logger.info("Campaign %s enqueued for execution", campaign_id)

        return campaign_id

    # ─── Read ────────────────────────────────────────────────────────────────

    def get_campaign(self, campaign_id: str) -> Campaign:
        """
        Retrieve a campaign by ID.

        Raises HTTP 404 if not found.
        """
        record = self._repo.get_by_id(campaign_id)
        # Check for None or empty dict (both indicate not found)
        if not record or (isinstance(record, dict) and not record):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found",
            )
        return Campaign(**record)

    def list_campaigns(self, page: int = 1, limit: int = 20) -> PaginatedResponse:
        """
        List campaigns with pagination (newest first).

        *page* is 1-indexed.
        """
        offset = (page - 1) * limit
        items_raw = self._repo.list_all(limit=limit, offset=offset)
        total = self._repo.count_all()
        total_pages = math.ceil(total / limit) if total else 1

        campaigns = [Campaign(**r) for r in items_raw]
        return PaginatedResponse(
            items=campaigns,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    def get_campaign_results(self, campaign_id: str) -> List[Tweet]:
        """
        Retrieve tweet results for a campaign.

        Raises HTTP 404 if the campaign does not exist.
        """
        # Verify campaign exists
        self.get_campaign(campaign_id)
        raw_all = self._repo.get_results(campaign_id)

        # Deduplicate by tweet_id to handle legacy duplicates and UI key warnings
        unique_raw = {}
        for r in raw_all:
            tid = r.get("tweet_id")
            if tid and tid not in unique_raw:
                unique_raw[tid] = r
        raw = list(unique_raw.values())

        # Map database fields to Tweet model fields
        tweets = []
        for r in raw:
            # Rename fields to match Tweet model
            tweet_data = {
                "id": r.get("tweet_id"),
                "url": r.get("tweet_url"),
                "author": r.get("author"),
                "text": r.get("text"),
                "likes": r.get("likes", 0),
                "reposts": r.get("reposts", 0),
                "replies": r.get("replies", 0),
                "timestamp": r.get("timestamp"),
            }
            tweets.append(Tweet(**tweet_data))

        return tweets

    def delete_campaign(self, campaign_id: str) -> None:
        """
        Delete a campaign and all its associated data.

        Raises HTTP 404 if the campaign does not exist.
        """
        # Verify campaign exists
        self.get_campaign(campaign_id)

        # Delete campaign (cascade will delete results and analysis)
        self._repo.delete(campaign_id)

    def retry_campaign(self, campaign_id: str) -> None:
        """
        Reset a campaign's state and re-enqueue it for execution.
        """
        # 1. Verify existence
        campaign = self.get_campaign(campaign_id)

        # 2. Reset status in DB
        self._repo.update_status(
            campaign_id,
            CampaignStatus.PENDING.value,
            error_message="",  # Clear error
            document_url="",  # Clear document
            results_count=0,  # Reset count
        )

        # 3. Delete existing child records for a clean retry
        self._repo.delete_results(campaign_id)
        self._repo.delete_analysis(campaign_id)

        if self._analysis_repo:
            self._analysis_repo.delete_by_campaign(campaign_id)

        if self._comment_repo:
            self._comment_repo.delete_by_campaign(campaign_id)

        # 4. Enqueue
        from src.workers.campaign_executor import execute_campaign  # noqa: PLC0415

        execute_campaign.delay(campaign_id)
        logger.info("Campaign %s re-enqueued for execution", campaign_id)
