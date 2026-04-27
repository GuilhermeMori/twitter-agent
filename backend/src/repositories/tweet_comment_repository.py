"""Tweet comment repository for database operations"""

from typing import List, Optional, Dict, Any
from supabase import Client
from src.core.logging_config import get_logger

logger = get_logger("repositories.tweet_comment_repository")


class TweetCommentRepository:
    """Repository for tweet comment database operations."""

    def __init__(self, db: Client) -> None:
        self._db = db

    def create(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tweet comment record.
        
        Args:
            comment_data: Dictionary with comment fields
            
        Returns:
            Created comment record
            
        Raises:
            Exception: If database operation fails
        """
        try:
            result = self._db.table("tweet_comments").insert(comment_data).execute()
            
            if not result.data:
                raise Exception("Failed to create tweet comment")
                
            logger.info("Created tweet comment: %s for tweet %s", 
                       result.data[0]["id"], comment_data["tweet_id"])
            return result.data[0]
            
        except Exception as e:
            logger.error("Failed to create tweet comment for tweet %s: %s", 
                        comment_data.get("tweet_id"), str(e))
            raise

    def get_by_id(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a tweet comment by ID.
        
        Args:
            comment_id: UUID string of the comment
            
        Returns:
            Comment record or None if not found
        """
        try:
            result = self._db.table("tweet_comments").select("*").eq("id", comment_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.info("Retrieved tweet comment: %s", comment_id)
                return result.data[0]
            
            logger.warning("Tweet comment not found: %s", comment_id)
            return None
            
        except Exception as e:
            logger.error("Failed to retrieve tweet comment %s: %s", comment_id, str(e))
            raise

    def get_by_campaign_and_tweet(self, campaign_id: str, tweet_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve valid comment for a specific tweet in a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            tweet_id: Twitter tweet ID
            
        Returns:
            Comment record or None if not found
        """
        try:
            result = (
                self._db.table("tweet_comments")
                .select("*")
                .eq("campaign_id", campaign_id)
                .eq("tweet_id", tweet_id)
                .eq("validation_status", "valid")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if result.data and len(result.data) > 0:
                logger.info("Retrieved comment for tweet %s in campaign %s", tweet_id, campaign_id)
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("Failed to retrieve comment for tweet %s in campaign %s: %s", 
                        tweet_id, campaign_id, str(e))
            raise

    def list_by_campaign(self, campaign_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all valid comments for a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of comment records
        """
        try:
            result = (
                self._db.table("tweet_comments")
                .select("*")
                .eq("campaign_id", campaign_id)
                .neq("validation_status", "regenerated")
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            logger.info("Listed %d comments for campaign %s", len(result.data), campaign_id)
            return result.data
            
        except Exception as e:
            logger.error("Failed to list comments for campaign %s: %s", campaign_id, str(e))
            raise

    def list_by_tweet_ids(self, campaign_id: str, tweet_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get comments for specific tweets in a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            tweet_ids: List of Twitter tweet IDs
            
        Returns:
            List of comment records
        """
        try:
            if not tweet_ids:
                return []
            
            result = (
                self._db.table("tweet_comments")
                .select("*")
                .eq("campaign_id", campaign_id)
                .neq("validation_status", "regenerated")
                .in_("tweet_id", tweet_ids)
                .order("created_at", desc=True)
                .execute()
            )
            
            logger.info("Retrieved %d comments for %d tweets in campaign %s", 
                       len(result.data), len(tweet_ids), campaign_id)
            return result.data
            
        except Exception as e:
            logger.error("Failed to get comments for tweets in campaign %s: %s", campaign_id, str(e))
            raise

    def mark_as_regenerated(self, campaign_id: str, tweet_id: str) -> bool:
        """
        Mark existing comments as regenerated for a tweet.
        
        Args:
            campaign_id: UUID string of the campaign
            tweet_id: Twitter tweet ID
            
        Returns:
            True if any comments were updated
        """
        try:
            result = (
                self._db.table("tweet_comments")
                .update({"validation_status": "regenerated", "updated_at": "now()"})
                .eq("campaign_id", campaign_id)
                .eq("tweet_id", tweet_id)
                .eq("validation_status", "valid")
                .execute()
            )
            
            updated_count = len(result.data) if result.data else 0
            logger.info("Marked %d comments as regenerated for tweet %s", updated_count, tweet_id)
            return updated_count > 0
            
        except Exception as e:
            logger.error("Failed to mark comments as regenerated for tweet %s: %s", tweet_id, str(e))
            raise

    def count_by_campaign(self, campaign_id: str) -> int:
        """
        Count total valid comments for a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            
        Returns:
            Total count of valid comments
        """
        try:
            result = (
                self._db.table("tweet_comments")
                .select("id", count="exact")
                .eq("campaign_id", campaign_id)
                .eq("validation_status", "valid")
                .execute()
            )
            
            count = result.count or 0
            logger.info("Campaign %s has %d valid comments", campaign_id, count)
            return count
            
        except Exception as e:
            logger.error("Failed to count comments for campaign %s: %s", campaign_id, str(e))
            raise

    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get comment statistics for a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Get all comments for the campaign (including failed ones)
            result = (
                self._db.table("tweet_comments")
                .select("validation_status, char_count, generation_attempt")
                .eq("campaign_id", campaign_id)
                .execute()
            )
            
            comments = result.data
            
            if not comments:
                return {
                    "total_comments": 0,
                    "valid_comments": 0,
                    "failed_comments": 0,
                    "regenerated_comments": 0,
                    "average_char_count": 0,
                    "max_attempts_used": 0
                }
            
            total = len(comments)
            valid = len([c for c in comments if c["validation_status"] == "valid"])
            failed = len([c for c in comments if c["validation_status"] == "failed"])
            regenerated = len([c for c in comments if c["validation_status"] == "regenerated"])
            
            valid_comments = [c for c in comments if c["validation_status"] == "valid"]
            avg_chars = sum(c["char_count"] for c in valid_comments) / len(valid_comments) if valid_comments else 0
            max_attempts = max(c["generation_attempt"] for c in comments) if comments else 0
            
            stats = {
                "total_comments": total,
                "valid_comments": valid,
                "failed_comments": failed,
                "regenerated_comments": regenerated,
                "average_char_count": round(avg_chars, 1),
                "max_attempts_used": max_attempts
            }
            
            logger.info("Campaign %s comment stats: %s", campaign_id, stats)
            return stats
            
        except Exception as e:
            logger.error("Failed to get comment stats for campaign %s: %s", campaign_id, str(e))
            raise

    def delete_by_campaign(self, campaign_id: str) -> int:
        """
        Delete all comments for a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            
        Returns:
            Number of deleted records
        """
        try:
            result = self._db.table("tweet_comments").delete().eq("campaign_id", campaign_id).execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info("Deleted %d comments for campaign %s", deleted_count, campaign_id)
            return deleted_count
            
        except Exception as e:
            logger.error("Failed to delete comments for campaign %s: %s", campaign_id, str(e))
            raise

    def get_comments_by_persona(self, persona_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent comments generated by a specific persona.
        
        Args:
            persona_id: UUID string of the persona
            limit: Maximum number of records to return
            
        Returns:
            List of comment records
        """
        try:
            result = (
                self._db.table("tweet_comments")
                .select("*")
                .eq("persona_id", persona_id)
                .eq("validation_status", "valid")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            logger.info("Retrieved %d comments for persona %s", len(result.data), persona_id)
            return result.data
            
        except Exception as e:
            logger.error("Failed to get comments for persona %s: %s", persona_id, str(e))
            raise