"""
Campaign progress tracking utility using Redis.
"""

import json
from typing import Optional, Dict, Any
from enum import Enum
import redis
from src.core.logging_config import get_logger
from src.core.config import settings

logger = get_logger("utils.progress_tracker")


class ProgressStage(str, Enum):
    """Campaign processing stages."""
    INITIALIZING = "initializing"
    SCRAPING = "scraping"
    ANALYZING = "analyzing"
    GENERATING_COMMENTS = "generating_comments"
    SELECTING_TOP_TWEETS = "selecting_top_tweets"
    GENERATING_EMAIL = "generating_email"
    GENERATING_DOCUMENT = "generating_document"
    COMPLETED = "completed"
    FAILED = "failed"


class CampaignProgressTracker:
    """Track campaign processing progress in Redis."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize progress tracker.
        
        Args:
            redis_client: Optional Redis client (creates one if not provided)
        """
        self._redis = redis_client or self._create_redis_client()
    
    def _create_redis_client(self) -> Optional[redis.Redis]:
        """Create Redis client from settings."""
        try:
            client = redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            logger.info("Redis connection established for progress tracking")
            return client
        except Exception as e:
            logger.warning("Failed to connect to Redis: %s. Progress tracking disabled.", str(e))
            return None
    
    def _get_key(self, campaign_id: str) -> str:
        """Get Redis key for campaign progress."""
        return f"campaign:progress:{campaign_id}"
    
    def update_progress(
        self,
        campaign_id: str,
        stage: ProgressStage,
        current: int = 0,
        total: int = 0,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update campaign progress.
        
        Args:
            campaign_id: UUID string of the campaign
            stage: Current processing stage
            current: Current item count (e.g., tweets processed)
            total: Total item count
            message: Optional progress message
            metadata: Optional additional metadata
        """
        if not self._redis:
            return
        
        try:
            progress_data = {
                "stage": stage.value,
                "current": current,
                "total": total,
                "percentage": round((current / total * 100) if total > 0 else 0, 1),
                "message": message or f"Processing {stage.value}",
                "metadata": metadata or {}
            }
            
            key = self._get_key(campaign_id)
            self._redis.setex(
                key,
                3600,  # Expire after 1 hour
                json.dumps(progress_data)
            )
            
            logger.debug(
                "Progress updated for campaign %s: %s (%d/%d)",
                campaign_id, stage.value, current, total
            )
            
        except Exception as e:
            logger.warning("Failed to update progress for campaign %s: %s", campaign_id, str(e))
    
    def get_progress(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get campaign progress.
        
        Args:
            campaign_id: UUID string of the campaign
            
        Returns:
            Progress data dictionary or None if not found
        """
        if not self._redis:
            return None
        
        try:
            key = self._get_key(campaign_id)
            data = self._redis.get(key)
            
            if data:
                return json.loads(data)
            
            return None
            
        except Exception as e:
            logger.warning("Failed to get progress for campaign %s: %s", campaign_id, str(e))
            return None
    
    def clear_progress(self, campaign_id: str) -> None:
        """
        Clear campaign progress.
        
        Args:
            campaign_id: UUID string of the campaign
        """
        if not self._redis:
            return
        
        try:
            key = self._get_key(campaign_id)
            self._redis.delete(key)
            logger.debug("Progress cleared for campaign %s", campaign_id)
            
        except Exception as e:
            logger.warning("Failed to clear progress for campaign %s: %s", campaign_id, str(e))
    
    def mark_stage_complete(
        self,
        campaign_id: str,
        stage: ProgressStage,
        message: Optional[str] = None
    ) -> None:
        """
        Mark a stage as complete (100%).
        
        Args:
            campaign_id: UUID string of the campaign
            stage: Completed stage
            message: Optional completion message
        """
        self.update_progress(
            campaign_id=campaign_id,
            stage=stage,
            current=1,
            total=1,
            message=message or f"{stage.value} completed"
        )
    
    def mark_failed(
        self,
        campaign_id: str,
        error_message: str
    ) -> None:
        """
        Mark campaign as failed.
        
        Args:
            campaign_id: UUID string of the campaign
            error_message: Error message
        """
        self.update_progress(
            campaign_id=campaign_id,
            stage=ProgressStage.FAILED,
            current=0,
            total=1,
            message=error_message
        )


# Global instance for shared progress tracking
_global_progress_tracker = CampaignProgressTracker()


def get_global_progress_tracker() -> CampaignProgressTracker:
    """Get the global progress tracker instance."""
    return _global_progress_tracker
