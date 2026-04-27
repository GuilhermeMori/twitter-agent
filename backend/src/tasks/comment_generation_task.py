"""
Comment Generation Celery Task

Async task that generates AI-powered comments for all tweets in a campaign
using the campaign's assigned persona (or the default persona if none is set).

Designed to run after tweet_analysis_task has completed (top-3 tweets are
already marked), but can also run independently.

Workflow:
1. Resolve the persona for the campaign
2. Load tweets from the database
3. Run CommentGenerationService.generate_comments_batch (async, OpenAI calls)
4. Update task progress at each step
5. Return a summary dict with counts

Retry policy: up to 3 attempts with exponential backoff on transient errors.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from celery.utils.log import get_task_logger
from openai import OpenAI

from src.workers.celery_app import celery_app
from src.workers.base_task import BaseTask
from src.core.database import get_supabase_client
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.tweet_comment_repository import TweetCommentRepository
from src.repositories.communication_style_repository import CommunicationStyleRepository
from src.repositories.assistant_repository import AssistantRepository
from src.repositories.configuration_repository import ConfigurationRepository
from src.services.configuration_manager import ConfigurationManager
from src.services.comment_generation_service import CommentGenerationService
from src.services.comment_validator import CommentValidator
from src.services.communication_style_service import CommunicationStyleService
from src.services.assistant_service import AssistantService
from src.models.campaign import Campaign, Tweet
from src.utils.encryption import Encryptor

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    base=BaseTask,
    name="comment_generation_task",
    max_retries=3,
)
def comment_generation_task(
    self,
    campaign_id: str,
    communication_style_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate comments for all tweets in *campaign_id*.

    If *communication_style_id* is None the campaign's own communication_style_id is used;
    if that is also absent the system default communication style is used.

    Returns a dict::

        {
            "campaign_id": str,
            "communication_style_id": str,
            "total_generated": int,
            "valid": int,
            "failed": int,
            "regenerated": int,
        }
    """
    return asyncio.run(_run(self, campaign_id, communication_style_id))


# ─── Async implementation ─────────────────────────────────────────────────────

async def _run(
    task_instance,
    campaign_id: str,
    communication_style_id: Optional[str],
) -> Dict[str, Any]:
    db = get_supabase_client()
    campaign_repo = CampaignRepository(db)
    comment_repo = TweetCommentRepository(db)
    cs_repo = CommunicationStyleRepository(db)
    cs_svc = CommunicationStyleService(cs_repo)
    assistant_repo = AssistantRepository(db)
    assistant_svc = AssistantService(assistant_repo)

    try:
        # ── 1. Load campaign ──────────────────────────────────────────────────
        logger.info("[comment_generation_task] Starting for campaign %s", campaign_id)
        task_instance.update_state(state="PROGRESS", meta={"step": "loading_campaign"})

        record = campaign_repo.get_by_id(campaign_id)
        if not record:
            raise RuntimeError(f"Campaign {campaign_id} not found")
        campaign = Campaign(**record)

        # ── 2. Resolve communication style ────────────────────────────────────
        task_instance.update_state(state="PROGRESS", meta={"step": "resolving_communication_style"})
        resolved_style_id = communication_style_id or (str(campaign.communication_style_id) if campaign.communication_style_id else None) or (str(campaign.persona_id) if campaign.persona_id else None)
        if not resolved_style_id:
            default = cs_svc.get_default_communication_style()
            resolved_style_id = str(default.id)
            logger.info(
                "[comment_generation_task] Using default communication style %s", resolved_style_id
            )
        else:
            logger.info(
                "[comment_generation_task] Using communication style %s", resolved_style_id
            )

        # ── 3. Load tweets ────────────────────────────────────────────────────
        task_instance.update_state(state="PROGRESS", meta={"step": "loading_tweets"})
        raw_tweets = campaign_repo.get_results(campaign_id)
        tweets: List[Tweet] = [
            Tweet(
                id=t["tweet_id"],
                url=t["tweet_url"],
                author=t["author"],
                text=t["text"],
                likes=t.get("likes", 0),
                reposts=t.get("reposts", 0),
                replies=t.get("replies", 0),
                timestamp=t["timestamp"],
            )
            for t in (raw_tweets or [])
        ]
        logger.info("[comment_generation_task] Loaded %d tweets", len(tweets))

        if not tweets:
            logger.warning(
                "[comment_generation_task] No tweets for campaign %s", campaign_id
            )
            return {
                "campaign_id": campaign_id,
                "communication_style_id": resolved_style_id,
                "total_generated": 0,
                "valid": 0,
                "failed": 0,
                "regenerated": 0,
            }

        # ── 4. Resolve OpenAI key ─────────────────────────────────────────────
        task_instance.update_state(state="PROGRESS", meta={"step": "resolving_config"})
        openai_api_key = _resolve_openai_key(db)

        # ── 5. Generate comments ──────────────────────────────────────────────
        task_instance.update_state(
            state="PROGRESS",
            meta={"step": "generating_comments", "total": len(tweets), "done": 0},
        )
        openai_client = OpenAI(api_key=openai_api_key)
        validator = CommentValidator()
        comment_service = CommentGenerationService(
            openai_client, cs_svc, assistant_svc, comment_repo, validator
        )

        comments = await comment_service.generate_comments_batch(
            tweets, resolved_style_id, campaign_id
        )
        logger.info("[comment_generation_task] Generated %d comments", len(comments))

        # ── 6. Build summary ──────────────────────────────────────────────────
        from src.models.tweet_comment import ValidationStatus
        valid = sum(1 for c in comments if c.validation_status == ValidationStatus.VALID)
        failed = sum(1 for c in comments if c.validation_status == ValidationStatus.FAILED)
        regenerated = sum(
            1 for c in comments if c.validation_status == ValidationStatus.REGENERATED
        )

        result = {
            "campaign_id": campaign_id,
            "communication_style_id": resolved_style_id,
            "total_generated": len(comments),
            "valid": valid,
            "failed": failed,
            "regenerated": regenerated,
        }
        logger.info("[comment_generation_task] Done: %s", result)
        return result

    except Exception as exc:
        logger.error(
            "[comment_generation_task] Error for campaign %s: %s",
            campaign_id,
            exc,
            exc_info=True,
        )
        if _is_transient(exc):
            task_instance.retry_with_backoff(exc)
        raise


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _resolve_openai_key(db) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    try:
        config_repo = ConfigurationRepository(db)
        encryptor = Encryptor()
        config = ConfigurationManager(config_repo, encryptor).get_configuration()
        if hasattr(config, "openai_token") and config.openai_token:
            return config.openai_token
    except Exception:
        pass
    raise RuntimeError("OpenAI API key not configured")


def _is_transient(exc: Exception) -> bool:
    indicators = ["timeout", "ratelimit", "unavailable", "connection", "network", "temporary"]
    msg = f"{type(exc).__name__} {exc}".lower()
    return any(i in msg for i in indicators)
