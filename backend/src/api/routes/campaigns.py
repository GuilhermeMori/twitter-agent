"""Campaign API routes"""

from fastapi import APIRouter, Depends, Query, status
from supabase import Client
from typing import List, Dict, Any, Optional

from src.core.database import get_db
from src.models.campaign import Campaign, CampaignCreateDTO, PaginatedResponse, Tweet
from src.models.tweet_analysis import TweetAnalysis
from src.models.tweet_comment import TweetComment
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.tweet_analysis_repository import TweetAnalysisRepository
from src.repositories.tweet_comment_repository import TweetCommentRepository
from src.services.campaign_service import CampaignService
from src.services.campaign_validator import CampaignValidator
from src.services.storage_service import StorageService
from src.core.logging_config import get_logger

logger = get_logger("api.routes.campaigns")

router = APIRouter()


# ─── New response models ─────────────────────────────────────────────────────

class TweetWithAnalysisAndComment(Tweet):
    """Tweet with analysis and comment data."""
    analysis: Optional[TweetAnalysis] = None
    comment: Optional[TweetComment] = None


class CampaignResultsResponse:
    """Enhanced campaign results with analysis and comments."""
    def __init__(
        self,
        tweets: List[TweetWithAnalysisAndComment],
        total_tweets: int,
        analysis_stats: Dict[str, Any],
        comment_stats: Dict[str, Any],
        top_3_tweet_ids: List[str]
    ):
        self.tweets = tweets
        self.total_tweets = total_tweets
        self.analysis_stats = analysis_stats
        self.comment_stats = comment_stats
        self.top_3_tweet_ids = top_3_tweet_ids


# ─── Dependency injection helpers ────────────────────────────────────────────

def get_campaign_service(db: Client = Depends(get_db)) -> CampaignService:
    """DI: CampaignService with all dependencies."""
    repo = CampaignRepository(db)
    analysis_repo = TweetAnalysisRepository(db)
    comment_repo = TweetCommentRepository(db)
    validator = CampaignValidator()
    return CampaignService(repo, validator, analysis_repo, comment_repo)


def get_storage_service(db: Client = Depends(get_db)) -> StorageService:
    """DI: StorageService."""
    return StorageService(db)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/campaigns",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new campaign",
    description="Validate, create, and enqueue a campaign for execution.",
)
async def create_campaign(
    data: CampaignCreateDTO,
    service: CampaignService = Depends(get_campaign_service),
) -> dict:
    """
    POST /api/campaigns

    Creates a new campaign, validates the input, and enqueues it for
    asynchronous execution by a Celery worker.

    Returns the new campaign's ID.
    Raises HTTP 400 on validation failure.
    """
    campaign_id = service.create_campaign(data)
    logger.info("Campaign created: %s", campaign_id)
    return {"campaign_id": campaign_id, "status": "pending"}


@router.get(
    "/campaigns",
    response_model=PaginatedResponse[Campaign],
    summary="List campaigns",
    description="Retrieve a paginated list of campaigns (newest first).",
)
async def list_campaigns(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: CampaignService = Depends(get_campaign_service),
) -> PaginatedResponse[Campaign]:
    """
    GET /api/campaigns?page=1&limit=20

    Returns a paginated list of campaigns ordered by creation date (newest first).
    """
    result = service.list_campaigns(page=page, limit=limit)
    logger.info("Listed campaigns: page=%d, limit=%d, total=%d", page, limit, result.total)
    return result


@router.get(
    "/campaigns/{campaign_id}",
    response_model=Campaign,
    summary="Get campaign details",
    description="Retrieve full details of a specific campaign.",
)
async def get_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> Campaign:
    """
    GET /api/campaigns/{id}

    Returns the campaign record including configuration, status, and metadata.
    Raises HTTP 404 if the campaign does not exist.
    """
    campaign = service.get_campaign(campaign_id)
    logger.info("Retrieved campaign: %s", campaign_id)
    return campaign


@router.get(
    "/campaigns/{campaign_id}/results",
    summary="Get campaign results with analysis and comments",
    description="Retrieve all tweets collected for a campaign with their analysis and comments.",
)
async def get_campaign_results(
    campaign_id: str,
    include_analysis: bool = Query(True, description="Include tweet analysis data"),
    include_comments: bool = Query(True, description="Include generated comments"),
    service: CampaignService = Depends(get_campaign_service),
    db: Client = Depends(get_db),
) -> Dict[str, Any]:
    """
    GET /api/campaigns/{id}/results?include_analysis=true&include_comments=true

    Returns enhanced campaign results including:
    - All tweets collected during the campaign
    - Tweet analysis scores and verdicts (if include_analysis=true)
    - Generated comments for each tweet (if include_comments=true)
    - Analysis and comment statistics
    - List of top 3 tweet IDs

    Raises HTTP 404 if the campaign does not exist.
    """
    # Get basic tweets
    tweets = service.get_campaign_results(campaign_id)
    
    # Initialize repositories for analysis and comments
    analysis_repo = TweetAnalysisRepository(db)
    comment_repo = TweetCommentRepository(db)
    
    # Get analysis and comments if requested
    analyses_dict = {}
    comments_dict = {}
    analysis_stats = {}
    comment_stats = {}
    top_3_tweet_ids = []
    
    if include_analysis:
        try:
            analyses = analysis_repo.list_by_campaign(campaign_id)
            analyses_dict = {a["tweet_id"]: TweetAnalysis(**a) for a in analyses}
            analysis_stats = analysis_repo.get_campaign_stats(campaign_id)
            
            # Get top 3 tweet IDs
            top_3_analyses = analysis_repo.get_top_3_tweets(campaign_id)
            top_3_tweet_ids = [a["tweet_id"] for a in top_3_analyses]
            
        except Exception as e:
            logger.warning("Failed to get analysis for campaign %s: %s", campaign_id, e)
    
    if include_comments:
        try:
            comments = comment_repo.list_by_campaign(campaign_id)
            comments_dict = {c["tweet_id"]: TweetComment(**c) for c in comments}
            comment_stats = comment_repo.get_campaign_stats(campaign_id)
            
        except Exception as e:
            logger.warning("Failed to get comments for campaign %s: %s", campaign_id, e)
    
    # Combine tweets with analysis and comments
    enhanced_tweets = []
    for tweet in tweets:
        enhanced_tweet_data = tweet.model_dump()
        
        # Add analysis if available
        if tweet.id in analyses_dict:
            enhanced_tweet_data["analysis"] = analyses_dict[tweet.id].model_dump()
        
        # Add comment if available
        if tweet.id in comments_dict:
            enhanced_tweet_data["comment"] = comments_dict[tweet.id].model_dump()
        
        enhanced_tweets.append(enhanced_tweet_data)

    # Sort: APPROVED first, then REJECTED, then those without analysis
    enhanced_tweets.sort(key=lambda x: (
        0 if x.get("analysis", {}).get("verdict") == "APPROVED" else 
        1 if x.get("analysis", {}).get("verdict") == "REJECTED" else 2
    ))

    # Update results_count in the campaign table if it mismatch the actual unique count
    actual_count = len(enhanced_tweets)
    try:
        # Get current campaign to check count
        campaign_obj = campaign_repo.get_by_id(campaign_id)
        if campaign_obj and campaign_obj.results_count != actual_count:
            campaign_repo.update(campaign_id, {"results_count": actual_count})
            logger.info("Updated results_count for campaign %s to %d", campaign_id, actual_count)
    except Exception as e:
        logger.warning("Failed to update results_count: %s", e)

    # Prepare response
    response = {
        "tweets": enhanced_tweets,
        "total_tweets": actual_count,
        "analysis_stats": analysis_stats,
        "comment_stats": comment_stats,
        "top_3_tweet_ids": top_3_tweet_ids,
        "has_analysis": include_analysis and bool(analyses_dict),
        "has_comments": include_comments and bool(comments_dict)
    }
    
    logger.info("Retrieved enhanced results for campaign %s: %d tweets, %d analyses, %d comments", 
               campaign_id, len(tweets), len(analyses_dict), len(comments_dict))
    
    return response


@router.get(
    "/campaigns/{campaign_id}/download",
    summary="Get document download URL",
    description="Generate a temporary signed URL for downloading the campaign document.",
)
async def get_download_url(
    campaign_id: str,
    storage: StorageService = Depends(get_storage_service),
    service: CampaignService = Depends(get_campaign_service),
) -> dict:
    """
    GET /api/campaigns/{id}/download

    Generates a temporary signed URL (valid for 1 hour) for downloading
    the campaign's .docx document.

    Raises HTTP 404 if the campaign or document does not exist.
    """
    # Verify campaign exists
    campaign = service.get_campaign(campaign_id)
    if not campaign.document_url:
        logger.warning("Campaign %s has no document", campaign_id)
        return {"error": "Document not available yet"}

    signed_url = storage.get_signed_url(campaign_id, expires_in=3600)
    logger.info("Generated download URL for campaign %s", campaign_id)
    return {"download_url": signed_url}


@router.delete(
    "/campaigns/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a campaign",
    description="Delete a campaign and all its associated data (results, analysis, document).",
)
async def delete_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
    storage: StorageService = Depends(get_storage_service),
) -> None:
    """
    DELETE /api/campaigns/{id}

    Deletes a campaign and all associated data:
    - Campaign record
    - Tweet results
    - Analysis
    - Document from storage

    Raises HTTP 404 if the campaign does not exist.
    """
    # Verify campaign exists
    campaign = service.get_campaign(campaign_id)
    
    # Delete document from storage if it exists
    if campaign.document_url:
        try:
            storage.delete_document(campaign_id)
            logger.info("Deleted document for campaign %s", campaign_id)
        except Exception as e:
            logger.warning("Failed to delete document for campaign %s: %s", campaign_id, e)
    
    # Delete campaign (cascade will delete results and analysis)
    service.delete_campaign(campaign_id)
    logger.info("Deleted campaign: %s", campaign_id)


@router.post(
    "/campaigns/{campaign_id}/retry",
    status_code=status.HTTP_200_OK,
    summary="Retry a campaign",
    description="Reset campaign status and re-enqueue for execution.",
)
async def retry_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
) -> dict:
    """
    POST /api/campaigns/{id}/retry

    Resets the status of a failed or completed campaign to 'pending'
    and enqueues it for re-execution.
    """
    service.retry_campaign(campaign_id)
    logger.info("Campaign retry triggered: %s", campaign_id)
    return {"status": "pending", "message": "Campaign re-enqueued for execution"}


@router.get(
    "/campaigns/{campaign_id}/top-results",
    summary="Get top 3 campaign results with analysis and comments",
    description="Retrieve the top 3 tweets for a campaign with their analysis and comments.",
)
async def get_top_campaign_results(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
    db: Client = Depends(get_db),
) -> Dict[str, Any]:
    """
    GET /api/campaigns/{id}/top-results

    Returns the top 3 tweets for a campaign with their analysis and comments.
    This is optimized for email generation and reporting.

    Raises HTTP 404 if the campaign does not exist.
    """
    # Verify campaign exists
    campaign = service.get_campaign(campaign_id)
    
    # Get repositories
    analysis_repo = TweetAnalysisRepository(db)
    comment_repo = TweetCommentRepository(db)
    
    try:
        # Get top 3 analyses
        top_analyses = analysis_repo.get_top_3_tweets(campaign_id)
        
        if not top_analyses:
            return {
                "top_tweets": [],
                "message": "No analyzed tweets found for this campaign"
            }
        
        # Get tweet IDs
        top_tweet_ids = [a["tweet_id"] for a in top_analyses]
        
        # Get the actual tweets
        all_tweets = service.get_campaign_results(campaign_id)
        tweets_dict = {tweet.id: tweet for tweet in all_tweets}
        
        # Get comments for these tweets
        comments = comment_repo.list_by_tweet_ids(campaign_id, top_tweet_ids)
        comments_dict = {c["tweet_id"]: TweetComment(**c) for c in comments}
        
        # Combine data
        top_results = []
        for analysis_data in top_analyses:
            tweet_id = analysis_data["tweet_id"]
            analysis = TweetAnalysis(**analysis_data)
            
            if tweet_id in tweets_dict:
                tweet = tweets_dict[tweet_id]
                comment = comments_dict.get(tweet_id)
                
                result = {
                    "tweet": tweet.model_dump(),
                    "analysis": analysis.model_dump(),
                    "comment": comment.model_dump() if comment else None
                }
                top_results.append(result)
        
        response = {
            "top_tweets": top_results,
            "total_top_tweets": len(top_results),
            "campaign_id": campaign_id,
            "campaign_name": campaign.name
        }
        
        logger.info("Retrieved top %d results for campaign %s", len(top_results), campaign_id)
        return response
        
    except Exception as e:
        logger.error("Failed to get top results for campaign %s: %s", campaign_id, e)
        return {
            "top_tweets": [],
            "error": f"Failed to retrieve top results: {str(e)}"
        }


@router.get(
    "/campaigns/{campaign_id}/progress",
    summary="Get campaign processing progress",
    description="Get real-time progress information for a campaign being processed"
)
def get_campaign_progress(
    campaign_id: str,
    db: Client = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get campaign processing progress.
    
    Returns progress information including:
    - Current processing stage
    - Progress percentage
    - Current/total items processed
    - Status message
    """
    try:
        from src.utils.progress_tracker import get_global_progress_tracker
        
        # Get progress from Redis
        tracker = get_global_progress_tracker()
        progress = tracker.get_progress(campaign_id)
        
        if not progress:
            # Check campaign status in database
            repo = CampaignRepository(db)
            campaign_data = repo.get_by_id(campaign_id)
            
            if not campaign_data:
                return {
                    "campaign_id": campaign_id,
                    "stage": "not_found",
                    "message": "Campaign not found",
                    "percentage": 0
                }
            
            campaign = Campaign(**campaign_data)
            
            # Return status based on campaign state
            if campaign.status == "completed":
                return {
                    "campaign_id": campaign_id,
                    "stage": "completed",
                    "message": "Campaign completed",
                    "percentage": 100,
                    "current": campaign.results_count,
                    "total": campaign.results_count
                }
            elif campaign.status == "failed":
                return {
                    "campaign_id": campaign_id,
                    "stage": "failed",
                    "message": campaign.error_message or "Campaign failed",
                    "percentage": 0
                }
            elif campaign.status == "pending":
                return {
                    "campaign_id": campaign_id,
                    "stage": "pending",
                    "message": "Campaign queued for processing",
                    "percentage": 0
                }
            else:
                return {
                    "campaign_id": campaign_id,
                    "stage": "running",
                    "message": "Campaign is being processed",
                    "percentage": 50
                }
        
        # Add campaign_id to progress data
        progress["campaign_id"] = campaign_id
        return progress
        
    except Exception as e:
        logger.error("Failed to get progress for campaign %s: %s", campaign_id, e)
        return {
            "campaign_id": campaign_id,
            "stage": "error",
            "message": f"Failed to retrieve progress: {str(e)}",
            "percentage": 0
        }
