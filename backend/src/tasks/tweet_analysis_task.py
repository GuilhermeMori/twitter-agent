"""
Tweet Analysis Celery Task

Async task that analyses a batch of tweets for a campaign using OpenAI.
Designed to run in parallel with comment_generation_task when both are needed.

Workflow:
1. Fetch tweets for the campaign from the database
2. Run TweetAnalysisService.analyze_tweets_batch (async, OpenAI calls)
3. Mark the top-N tweets by average score
4. Update task progress at each step
5. Return a summary dict with counts and top-tweet IDs

Retry policy: up to 3 attempts with exponential backoff on transient errors.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List

from celery.utils.log import get_task_logger
from openai import OpenAI

from src.workers.celery_app import celery_app
from src.workers.base_task import BaseTask
from src.core.database import get_supabase_client
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.tweet_analysis_repository import TweetAnalysisRepository
from src.repositories.configuration_repository import ConfigurationRepository
from src.services.configuration_manager import ConfigurationManager
from src.services.tweet_analysis_service import TweetAnalysisService
from src.models.campaign import Campaign, Tweet
from src.utils.encryption import Encryptor

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    base=BaseTask,
    name="tweet_analysis_task",
    max_retries=3,
)
def tweet_analysis_task(
    self,
    campaign_id: str,
    top_n: int = 3,
) -> Dict[str, Any]:
    """
    Analyse all tweets for *campaign_id* and mark the top *top_n* by score.

    Returns a dict::

        {
            "campaign_id": str,
            "total_analysed": int,
            "approved": int,
            "rejected": int,
            "top_tweet_ids": list[str],
        }
    """
    return asyncio.run(_run(self, campaign_id, top_n))


# ─── Async implementation ─────────────────────────────────────────────────────


async def _run(task_instance, campaign_id: str, top_n: int) -> Dict[str, Any]:
    db = get_supabase_client()
    campaign_repo = CampaignRepository(db)
    analysis_repo = TweetAnalysisRepository(db)

    try:
        # ── 1. Load campaign ──────────────────────────────────────────────────
        logger.info("[tweet_analysis_task] Starting for campaign %s", campaign_id)
        task_instance.update_state(state="PROGRESS", meta={"step": "loading_campaign"})

        record = campaign_repo.get_by_id(campaign_id)
        if not record:
            raise RuntimeError(f"Campaign {campaign_id} not found")
        campaign = Campaign(**record)

        # ── 2. Load tweets from DB ────────────────────────────────────────────
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
        logger.info("[tweet_analysis_task] Loaded %d tweets", len(tweets))

        if not tweets:
            logger.warning(
                "[tweet_analysis_task] No tweets to analyse for campaign %s", campaign_id
            )
            return {
                "campaign_id": campaign_id,
                "total_analysed": 0,
                "approved": 0,
                "rejected": 0,
                "top_tweet_ids": [],
            }

        # ── 3. Resolve OpenAI key ─────────────────────────────────────────────
        task_instance.update_state(state="PROGRESS", meta={"step": "resolving_config"})
        openai_api_key = _resolve_openai_key(db)

        # ── 4. Run analysis ───────────────────────────────────────────────────
        task_instance.update_state(
            state="PROGRESS",
            meta={"step": "analysing_tweets", "total": len(tweets), "done": 0},
        )
        openai_client = OpenAI(api_key=openai_api_key)
        analysis_service = TweetAnalysisService(openai_client, analysis_repo)

        analyses = await analysis_service.analyze_tweets_batch(tweets, campaign_id)
        logger.info("[tweet_analysis_task] Analysed %d tweets", len(analyses))

        # ── 5. Mark top-N ─────────────────────────────────────────────────────
        task_instance.update_state(state="PROGRESS", meta={"step": "marking_top_tweets"})
        top_analyses = analysis_service.mark_top_tweets(campaign_id, top_n)
        top_ids = [a.tweet_id for a in top_analyses]
        logger.info("[tweet_analysis_task] Marked %d top tweets: %s", len(top_ids), top_ids)

        # ── 6. Build summary ──────────────────────────────────────────────────
        from src.models.tweet_analysis import Verdict

        approved = sum(1 for a in analyses if a.verdict == Verdict.APPROVED)
        rejected = len(analyses) - approved

        result = {
            "campaign_id": campaign_id,
            "total_analysed": len(analyses),
            "approved": approved,
            "rejected": rejected,
            "top_tweet_ids": top_ids,
        }
        logger.info("[tweet_analysis_task] Done: %s", result)
        return result

    except Exception as exc:
        logger.error(
            "[tweet_analysis_task] Error for campaign %s: %s",
            campaign_id,
            exc,
            exc_info=True,
        )
        if _is_transient(exc):
            task_instance.retry_with_backoff(exc)
        raise


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _resolve_openai_key(db) -> str:
    """Return the OpenAI API key from config or environment."""
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
