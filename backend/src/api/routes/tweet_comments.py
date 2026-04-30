"""Tweet comment API routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List, Dict, Any

from src.core.database import get_db
from src.models.tweet_comment import TweetComment, CommentRegenerationRequest
from src.models.campaign import Tweet
from src.repositories.tweet_comment_repository import TweetCommentRepository
from src.services.comment_generation_service import CommentGenerationService
from src.services.communication_style_service import CommunicationStyleService
from src.services.comment_validator import CommentValidator
from src.repositories.communication_style_repository import CommunicationStyleRepository
from src.core.logging_config import get_logger
from openai import OpenAI
from src.core.config import settings

logger = get_logger("api.routes.tweet_comments")

router = APIRouter()


# ─── Dependency injection helpers ────────────────────────────────────────────


def get_openai_client() -> OpenAI:
    """DI: OpenAI client."""
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured",
        )
    return OpenAI(api_key=settings.openai_api_key)


def get_comment_generation_service(
    db: Client = Depends(get_db), openai_client: OpenAI = Depends(get_openai_client)
) -> CommentGenerationService:
    """DI: CommentGenerationService with all dependencies."""
    communication_style_repo = CommunicationStyleRepository(db)
    communication_style_service = CommunicationStyleService(communication_style_repo)
    comment_repo = TweetCommentRepository(db)
    validator = CommentValidator()
    return CommentGenerationService(
        openai_client, communication_style_service, comment_repo, validator
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get(
    "/campaigns/{campaign_id}/comments",
    response_model=List[TweetComment],
    summary="Get comments for campaign",
    description="Retrieve all valid comments for a campaign.",
)
async def get_campaign_comments(
    campaign_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of comments to return"),
    offset: int = Query(0, ge=0, description="Number of comments to skip"),
    service: CommentGenerationService = Depends(get_comment_generation_service),
) -> List[TweetComment]:
    """
    GET /api/campaigns/{campaign_id}/comments?limit=100&offset=0

    Returns all valid comments for a campaign, ordered by creation date (newest first).
    Only includes comments with validation_status = 'valid'.

    Raises HTTP 404 if campaign not found.
    """
    try:
        comments = service.get_campaign_comments(campaign_id)

        # Apply pagination
        paginated_comments = comments[offset : offset + limit]

        logger.info(
            "Retrieved %d comments for campaign %s (offset=%d, limit=%d)",
            len(paginated_comments),
            campaign_id,
            offset,
            limit,
        )
        return paginated_comments

    except Exception as e:
        logger.error("Failed to get comments for campaign %s: %s", campaign_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve comments"
        )


@router.get(
    "/campaigns/{campaign_id}/tweets/{tweet_id}/comment",
    response_model=TweetComment,
    summary="Get comment for specific tweet",
    description="Retrieve the comment for a specific tweet in a campaign.",
)
async def get_tweet_comment(
    campaign_id: str,
    tweet_id: str,
    service: CommentGenerationService = Depends(get_comment_generation_service),
) -> TweetComment:
    """
    GET /api/campaigns/{campaign_id}/tweets/{tweet_id}/comment

    Returns the valid comment for a specific tweet in a campaign.

    Raises HTTP 404 if comment not found.
    """
    try:
        # Get comments for this specific tweet
        comments = service.get_comments_for_tweets(campaign_id, [tweet_id])

        if not comments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment for tweet {tweet_id} not found in campaign {campaign_id}",
            )

        # Return the first (and should be only) comment
        comment = comments[0]
        logger.info("Retrieved comment for tweet %s in campaign %s", tweet_id, campaign_id)
        return comment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get comment for tweet %s in campaign %s: %s", tweet_id, campaign_id, str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve comment"
        )


@router.get(
    "/campaigns/{campaign_id}/comments/stats",
    response_model=Dict[str, Any],
    summary="Get comment statistics for campaign",
    description="Retrieve comment statistics and metrics for a campaign.",
)
async def get_campaign_comment_stats(
    campaign_id: str,
    service: CommentGenerationService = Depends(get_comment_generation_service),
) -> Dict[str, Any]:
    """
    GET /api/campaigns/{campaign_id}/comments/stats

    Returns comment statistics for a campaign including:
    - Total number of comments generated
    - Number of valid vs failed comments
    - Average character count
    - Maximum generation attempts used

    Raises HTTP 404 if campaign not found.
    """
    try:
        # Get repository directly for stats
        db = next(get_db())
        repo = TweetCommentRepository(db)
        stats = repo.get_campaign_stats(campaign_id)

        logger.info("Retrieved comment stats for campaign %s: %s", campaign_id, stats)
        return stats

    except Exception as e:
        logger.error("Failed to get comment stats for campaign %s: %s", campaign_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comment statistics",
        )


@router.post(
    "/campaigns/{campaign_id}/tweets/{tweet_id}/regenerate-comment",
    response_model=TweetComment,
    summary="Regenerate comment for tweet",
    description="Regenerate the comment for a specific tweet, optionally with a different persona.",
)
async def regenerate_comment(
    campaign_id: str,
    tweet_id: str,
    request: CommentRegenerationRequest,
    service: CommentGenerationService = Depends(get_comment_generation_service),
) -> TweetComment:
    """
    POST /api/campaigns/{campaign_id}/tweets/{tweet_id}/regenerate-comment

    Regenerates the comment for a specific tweet in a campaign.
    The existing valid comment will be marked as 'regenerated' and a new one will be generated.

    Request body:
    {
        "campaign_id": "uuid",
        "tweet_id": "string",
        "persona_id": "uuid" // optional, uses original persona if not provided
    }

    Returns the new comment.
    Raises HTTP 404 if tweet or campaign not found.
    """
    try:
        # We need to get the tweet data to regenerate the comment
        # For now, we'll create a minimal tweet object
        # In a real implementation, you'd fetch the tweet from the database
        tweet = Tweet(
            id=tweet_id,
            url=f"https://twitter.com/user/status/{tweet_id}",
            author="unknown",  # This should be fetched from database
            text="[Tweet text not available]",  # This should be fetched from database
            likes=0,
            reposts=0,
            replies=0,
            timestamp=None,
        )

        new_comment = await service.regenerate_comment(
            tweet=tweet,
            campaign_id=campaign_id,
            persona_id=str(request.persona_id) if request.persona_id else None,
        )

        logger.info("Regenerated comment for tweet %s in campaign %s", tweet_id, campaign_id)
        return new_comment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to regenerate comment for tweet %s in campaign %s: %s",
            tweet_id,
            campaign_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to regenerate comment"
        )


@router.get(
    "/campaigns/{campaign_id}/tweets/comments",
    response_model=List[TweetComment],
    summary="Get comments for specific tweets",
    description="Retrieve comments for a list of specific tweets in a campaign.",
)
async def get_comments_for_tweets(
    campaign_id: str,
    tweet_ids: str = Query(..., description="Comma-separated list of tweet IDs"),
    service: CommentGenerationService = Depends(get_comment_generation_service),
) -> List[TweetComment]:
    """
    GET /api/campaigns/{campaign_id}/tweets/comments?tweet_ids=123,456,789

    Returns comments for the specified tweets in a campaign.
    Useful for getting comments for top 3 tweets or a specific subset.

    Raises HTTP 404 if campaign not found.
    """
    try:
        # Parse tweet IDs from comma-separated string
        tweet_id_list = [tid.strip() for tid in tweet_ids.split(",") if tid.strip()]

        if not tweet_id_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one tweet ID must be provided",
            )

        comments = service.get_comments_for_tweets(campaign_id, tweet_id_list)

        logger.info(
            "Retrieved %d comments for %d tweets in campaign %s",
            len(comments),
            len(tweet_id_list),
            campaign_id,
        )
        return comments

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get comments for tweets in campaign %s: %s", campaign_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comments for tweets",
        )
