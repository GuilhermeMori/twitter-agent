"""Tweet analysis API routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List, Dict, Any

from src.core.database import get_db
from src.models.tweet_analysis import TweetAnalysis, TweetAnalysisSummary
from src.repositories.tweet_analysis_repository import TweetAnalysisRepository
from src.services.tweet_analysis_service import TweetAnalysisService
from src.core.logging_config import get_logger
from openai import OpenAI
from src.core.config import settings

logger = get_logger("api.routes.tweet_analysis")

router = APIRouter()


# ─── Dependency injection helpers ────────────────────────────────────────────

def get_openai_client() -> OpenAI:
    """DI: OpenAI client."""
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured"
        )
    return OpenAI(api_key=settings.openai_api_key)


def get_tweet_analysis_service(
    db: Client = Depends(get_db),
    openai_client: OpenAI = Depends(get_openai_client)
) -> TweetAnalysisService:
    """DI: TweetAnalysisService with all dependencies."""
    repo = TweetAnalysisRepository(db)
    return TweetAnalysisService(openai_client, repo)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get(
    "/campaigns/{campaign_id}/analysis",
    response_model=List[TweetAnalysis],
    summary="Get tweet analyses for campaign",
    description="Retrieve all tweet analyses for a campaign, ordered by score (highest first).",
)
async def get_campaign_analysis(
    campaign_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of analyses to return"),
    offset: int = Query(0, ge=0, description="Number of analyses to skip"),
    service: TweetAnalysisService = Depends(get_tweet_analysis_service),
) -> List[TweetAnalysis]:
    """
    GET /api/campaigns/{campaign_id}/analysis?limit=100&offset=0

    Returns all tweet analyses for a campaign, ordered by average score (highest first).
    Includes detailed scoring breakdown and analysis notes.
    
    Raises HTTP 404 if campaign not found.
    """
    try:
        analyses = service.get_campaign_analyses(campaign_id)
        
        # Apply pagination
        paginated_analyses = analyses[offset:offset + limit]
        
        logger.info("Retrieved %d analyses for campaign %s (offset=%d, limit=%d)", 
                   len(paginated_analyses), campaign_id, offset, limit)
        return paginated_analyses
        
    except Exception as e:
        logger.error("Failed to get analyses for campaign %s: %s", campaign_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tweet analyses"
        )


@router.get(
    "/campaigns/{campaign_id}/top-tweets",
    response_model=List[TweetAnalysis],
    summary="Get top tweets for campaign",
    description="Retrieve the top-scoring tweets for a campaign.",
)
async def get_top_tweets(
    campaign_id: str,
    limit: int = Query(3, ge=1, le=10, description="Number of top tweets to return"),
    service: TweetAnalysisService = Depends(get_tweet_analysis_service),
) -> List[TweetAnalysis]:
    """
    GET /api/campaigns/{campaign_id}/top-tweets?limit=3

    Returns the top N tweets by average score for a campaign.
    These are the tweets that should be featured in emails and reports.
    
    Raises HTTP 404 if campaign not found.
    """
    try:
        if limit <= 3:
            # Use the pre-marked top 3 tweets if requesting 3 or fewer
            analyses = service.get_top_3_tweets(campaign_id)
            return analyses[:limit]
        else:
            # Get top N tweets dynamically
            all_analyses = service.get_campaign_analyses(campaign_id)
            return all_analyses[:limit]
        
    except Exception as e:
        logger.error("Failed to get top tweets for campaign %s: %s", campaign_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top tweets"
        )


@router.get(
    "/campaigns/{campaign_id}/analysis/stats",
    response_model=Dict[str, Any],
    summary="Get analysis statistics for campaign",
    description="Retrieve analysis statistics and metrics for a campaign.",
)
async def get_campaign_analysis_stats(
    campaign_id: str,
    service: TweetAnalysisService = Depends(get_tweet_analysis_service),
) -> Dict[str, Any]:
    """
    GET /api/campaigns/{campaign_id}/analysis/stats

    Returns analysis statistics for a campaign including:
    - Total number of tweets analyzed
    - Number of approved vs rejected tweets
    - Average score across all tweets
    - Number of top 3 tweets marked
    
    Raises HTTP 404 if campaign not found.
    """
    try:
        stats = service.get_campaign_stats(campaign_id)
        
        logger.info("Retrieved analysis stats for campaign %s: %s", campaign_id, stats)
        return stats
        
    except Exception as e:
        logger.error("Failed to get analysis stats for campaign %s: %s", campaign_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis statistics"
        )


@router.get(
    "/campaigns/{campaign_id}/tweets/{tweet_id}/analysis",
    response_model=TweetAnalysis,
    summary="Get analysis for specific tweet",
    description="Retrieve analysis for a specific tweet in a campaign.",
)
async def get_tweet_analysis(
    campaign_id: str,
    tweet_id: str,
    service: TweetAnalysisService = Depends(get_tweet_analysis_service),
) -> TweetAnalysis:
    """
    GET /api/campaigns/{campaign_id}/tweets/{tweet_id}/analysis

    Returns the analysis for a specific tweet in a campaign.
    
    Raises HTTP 404 if tweet analysis not found.
    """
    try:
        # Get all analyses and find the specific one
        analyses = service.get_campaign_analyses(campaign_id)
        
        for analysis in analyses:
            if analysis.tweet_id == tweet_id:
                logger.info("Retrieved analysis for tweet %s in campaign %s", tweet_id, campaign_id)
                return analysis
        
        # Not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis for tweet {tweet_id} not found in campaign {campaign_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get analysis for tweet %s in campaign %s: %s", 
                    tweet_id, campaign_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tweet analysis"
        )


@router.post(
    "/campaigns/{campaign_id}/analysis/mark-top-tweets",
    response_model=List[TweetAnalysis],
    summary="Mark top tweets for campaign",
    description="Mark the top N tweets as featured for a campaign.",
)
async def mark_top_tweets(
    campaign_id: str,
    top_n: int = Query(3, ge=1, le=10, description="Number of top tweets to mark"),
    service: TweetAnalysisService = Depends(get_tweet_analysis_service),
) -> List[TweetAnalysis]:
    """
    POST /api/campaigns/{campaign_id}/analysis/mark-top-tweets?top_n=3

    Marks the top N tweets by score as featured tweets for the campaign.
    This updates the is_top_3 flag in the database.
    
    Returns the marked tweet analyses.
    Raises HTTP 404 if campaign not found.
    """
    try:
        marked_analyses = service.mark_top_tweets(campaign_id, top_n)
        
        logger.info("Marked %d top tweets for campaign %s", len(marked_analyses), campaign_id)
        return marked_analyses
        
    except Exception as e:
        logger.error("Failed to mark top tweets for campaign %s: %s", campaign_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark top tweets"
        )