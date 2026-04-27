"""
Campaign Executor — Celery task that orchestrates full campaign execution.

Workflow:
1. Update status → running
2. Retrieve configuration (credentials)
3. Scrape tweets via Apify
4. Save tweets to DB
5. Analyze tweets with OpenAI (5 criteria scoring)
6. Generate comments using selected persona
7. Mark top 3 tweets
8. Generate .docx document with analysis and comments
9. Send email with top 3 tweets and comments
10. Upload document to Supabase Storage
11. Update status → completed (with document URL)

On error at any step: update status → failed (with error message).
Implements exponential backoff retry (max 3 attempts).
"""

from __future__ import annotations

import os
import asyncio
from typing import List

from openai import OpenAI
from celery.utils.log import get_task_logger

from src.workers.celery_app import celery_app
from src.workers.base_task import BaseTask
from src.core.database import get_supabase_client
from src.models.campaign import Campaign, ScrapingConfig, Tweet, CampaignStatus
from src.models.analysis import Analysis
from src.models.tweet_analysis import TweetAnalysis
from src.models.tweet_comment import TweetComment
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.tweet_analysis_repository import TweetAnalysisRepository
from src.repositories.tweet_comment_repository import TweetCommentRepository
from src.repositories.communication_style_repository import CommunicationStyleRepository
from src.repositories.assistant_repository import AssistantRepository
from src.services.configuration_manager import ConfigurationManager
from src.services.scraping_engine import ScrapingEngineFactory
from src.services.analysis_engine import AnalysisEngine
from src.services.tweet_analysis_service import TweetAnalysisService
from src.services.comment_generation_service import CommentGenerationService
from src.services.communication_style_service import CommunicationStyleService
from src.services.assistant_service import AssistantService
from src.services.comment_validator import CommentValidator
from src.services.document_generator import DocumentGenerator
from src.services.email_service import EmailService
from src.services.storage_service import StorageService
from src.repositories.configuration_repository import ConfigurationRepository
from src.utils.encryption import Encryptor

logger = get_task_logger(__name__)


@celery_app.task(bind=True, base=BaseTask, name="execute_campaign")
def execute_campaign(self, campaign_id: str) -> None:
    """
    Execute a complete campaign workflow.

    This task is enqueued by CampaignService.create_campaign().
    Retries up to 3 times with exponential backoff on transient failures.
    """
    # Run the async workflow
    asyncio.run(_execute_campaign_async(self, campaign_id))


async def _execute_campaign_async(task_instance, campaign_id: str) -> None:
    """
    Async implementation of campaign execution workflow.
    """
    db = get_supabase_client()
    repo = CampaignRepository(db)

    try:
        # ─── Step 1: Update status → running ─────────────────────────────────
        logger.info("Starting campaign execution: %s", campaign_id)
        repo.update_status(campaign_id, "running")

        # ─── Step 2: Retrieve configuration ───────────────────────────────────
        config_repo = ConfigurationRepository(db)
        encryptor = Encryptor()
        config_mgr = ConfigurationManager(config_repo, encryptor)
        config = config_mgr.get_configuration()
        logger.info("Configuration retrieved for campaign %s", campaign_id)

        # ─── Step 3: Scrape tweets ────────────────────────────────────────────
        campaign_record = repo.get_by_id(campaign_id)
        if not campaign_record:
            raise RuntimeError(f"Campaign {campaign_id} not found in database")
        campaign = Campaign(**campaign_record)

        scraping_config = ScrapingConfig(
            search_type=campaign.search_type,
            profiles=campaign.config.profiles,
            keywords=campaign.config.keywords,
            language=campaign.config.language,
            min_likes=campaign.config.min_likes,
            min_retweets=campaign.config.min_retweets,
            min_replies=campaign.config.min_replies,
            days_back=campaign.config.days_back,
            apify_token=config.apify_token,
            twitter_auth_token=config.twitter_auth_token,
            twitter_ct0=config.twitter_ct0,
        )

        scraping_engine = ScrapingEngineFactory.create(
            campaign.social_network, config.apify_token
        )
        tweets: List[Tweet] = scraping_engine.scrape(scraping_config)
        
        # Deduplicate tweets by ID (unique tweet_id)
        unique_tweets = {}
        for t in tweets:
            unique_tweets[t.id] = t
        tweets = list(unique_tweets.values())
        
        logger.info("Scraped %d unique tweets for campaign %s", len(tweets), campaign_id)

        # ─── Step 4: Save tweets ──────────────────────────────────────────────
        # Map Tweet model fields to database column names
        tweet_dicts = []
        for t in tweets:
            tweet_dict = t.model_dump(mode='json')
            # Rename fields to match database schema
            tweet_dict['tweet_id'] = tweet_dict.pop('id')
            tweet_dict['tweet_url'] = tweet_dict.pop('url')
            tweet_dicts.append(tweet_dict)
        
        repo.save_results(campaign_id, tweet_dicts)
        logger.info("Saved %d tweet results to DB", len(tweets))

        # ─── Step 5 & 6: Analyze and Comment (Optional) ────────────────────────
        # Only run Rita (Step 5) and Cadu (Step 6) if a communication style is selected.
        # Otherwise, "Somente o Beto" (search only) rule applies.
        communication_style_id = str(campaign.communication_style_id) if campaign.communication_style_id else (str(campaign.persona_id) if campaign.persona_id else None)
        
        # Use OpenAI API key from environment or configuration
        openai_api_key = config.openai_token if hasattr(config, 'openai_token') else os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise RuntimeError("OpenAI API key not configured")
            
        openai_client = OpenAI(api_key=openai_api_key)

        all_analyses = []
        all_comments = []
        legacy_analysis = None
        style_obj = None

        if communication_style_id:
            # ─── Step 5: Analyze tweets with OpenAI (Rita) ───────────────────
            # Initialize analysis service
            analysis_repo = TweetAnalysisRepository(db)
            tweet_analysis_service = TweetAnalysisService(openai_client, analysis_repo)
            
            # Analyze tweets (this will save to database automatically)
            logger.info("Starting tweet analysis for %d tweets", len(tweets))
            await tweet_analysis_service.analyze_tweets_batch(tweets, campaign_id)
            
            # Mark top 3 tweets
            tweet_analysis_service.mark_top_tweets(campaign_id, 3)
            
            # Retrieve analyses for later steps
            all_analyses = tweet_analysis_service.get_campaign_analyses(campaign_id)

            # ─── Step 6: Generate comments using communication style (Cadu) ──
            # Initialize services
            cs_repo = CommunicationStyleRepository(db)
            cs_service = CommunicationStyleService(cs_repo)
            assistant_repo = AssistantRepository(db)
            assistant_service = AssistantService(assistant_repo)
            comment_repo = TweetCommentRepository(db)
            validator = CommentValidator()
            comment_service = CommentGenerationService(
                openai_client, 
                cs_service,
                assistant_service,
                comment_repo, 
                validator
            )
            
            # Generate comments for all tweets
            logger.info("Starting comment generation for %d tweets", len(tweets))
            await comment_service.generate_comments_batch(tweets, communication_style_id, campaign_id)
            
            # Retrieve comments and style object for later steps
            all_comments = comment_service.get_campaign_comments(campaign_id)
            
            try:
                style_obj = cs_service.get_communication_style(communication_style_id)
            except Exception:
                pass
            # ─── Step 7: Legacy analysis for document compatibility ───────────
            # Keep the old analysis for backward compatibility with document generator
            analysis_engine = AnalysisEngine(openai_client)
            legacy_analysis = analysis_engine.analyze(tweets)
            analysis_text = legacy_analysis.model_dump_json()
            repo.save_analysis(campaign_id, analysis_text)
            logger.info("Legacy analysis saved for document compatibility")
        else:
            logger.info("No communication style selected. Skipping Rita, Cadu, and Legacy Analysis.")


        doc_gen = DocumentGenerator()
        doc_path = doc_gen.generate(
            campaign,
            tweets,
            legacy_analysis,
            tweet_analyses=all_analyses,
            tweet_comments=all_comments,
            persona=style_obj,
        )
        logger.info("Document generated at %s", doc_path)

        # ─── Step 9: Send email ───────────────────────────────────────────────
        # Collect top-3 tweet objects for the email
        top3_tweet_ids = {a.tweet_id for a in all_analyses if a.is_top_3}
        top3_tweets = [t for t in tweets if t.id in top3_tweet_ids]
        top3_analyses = [a for a in all_analyses if a.is_top_3]
        top3_comments = [c for c in all_comments if c.tweet_id in top3_tweet_ids]

        # Update campaign object in memory for the email service
        campaign.results_count = len(tweets)

        email_service = EmailService(config.user_email, config.smtp_password)
        email_service.send_campaign_results(
            config.user_email,
            campaign,
            doc_path,
            top_tweets=top3_tweets,
            top_analyses=top3_analyses,
            top_comments=top3_comments,
        )
        logger.info("Email sent to %s", config.user_email)

        # ─── Step 10: Upload to storage ───────────────────────────────────────
        storage_service = StorageService(db)
        document_url = storage_service.upload_document(campaign_id, doc_path)
        logger.info("Document uploaded to storage: %s", document_url)

        # Clean up temp file
        try:
            os.remove(doc_path)
            logger.debug("Temporary file removed: %s", doc_path)
        except OSError as exc:
            logger.warning("Could not remove temp file %s: %s", doc_path, exc)

        # ─── Step 11: Update status → completed ───────────────────────────────
        repo.update_status(
            campaign_id,
            "completed",
            document_url=document_url,
            results_count=len(tweets),
        )
        logger.info("Campaign %s completed successfully", campaign_id)

    except Exception as exc:
        # ─── Error handling: update status → failed ──────────────────────────
        error_msg = f"{type(exc).__name__}: {str(exc)}"
        logger.error("Campaign %s failed: %s", campaign_id, error_msg, exc_info=True)
        try:
            repo.update_status(campaign_id, "failed", error_message=error_msg)
        except Exception as update_exc:
            logger.error("Failed to update campaign status: %s", update_exc)

        # Retry on transient errors (network, rate limits, etc.)
        if _is_transient_error(exc):
            logger.info("Transient error detected — retrying campaign %s", campaign_id)
            task_instance.retry_with_backoff(exc)
        else:
            # Permanent error — do not retry
            logger.error("Permanent error — not retrying campaign %s", campaign_id)
            raise


def _is_transient_error(exc: Exception) -> bool:
    """
    Return True if *exc* is likely a transient error that may succeed on retry.

    Examples: network timeouts, rate limits, temporary service unavailability.
    """
    exc_name = type(exc).__name__
    transient_indicators = [
        "timeout",
        "ratelimit",
        "unavailable",
        "connection",
        "network",
        "temporary",
    ]
    return any(indicator in exc_name.lower() or indicator in str(exc).lower() for indicator in transient_indicators)
