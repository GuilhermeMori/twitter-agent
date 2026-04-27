"""Tweet analysis repository for database operations"""

from typing import List, Optional, Dict, Any
from supabase import Client
from src.core.logging_config import get_logger

logger = get_logger("repositories.tweet_analysis_repository")


class TweetAnalysisRepository:
    """Repository for tweet analysis database operations."""

    def __init__(self, db: Client) -> None:
        self._db = db

    def create(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tweet analysis record.
        
        Args:
            analysis_data: Dictionary with analysis fields
            
        Returns:
            Created analysis record
            
        Raises:
            Exception: If database operation fails
        """
        try:
            result = self._db.table("tweet_analysis").insert(analysis_data).execute()
            
            if not result.data:
                raise Exception("Failed to create tweet analysis")
                
            logger.info("Created tweet analysis: %s for tweet %s", 
                       result.data[0]["id"], analysis_data["tweet_id"])
            return result.data[0]
            
        except Exception as e:
            logger.error("Failed to create tweet analysis for tweet %s: %s", 
                        analysis_data.get("tweet_id"), str(e))
            raise

    def get_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a tweet analysis by ID.
        
        Args:
            analysis_id: UUID string of the analysis
            
        Returns:
            Analysis record or None if not found
        """
        try:
            result = self._db.table("tweet_analysis").select("*").eq("id", analysis_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.info("Retrieved tweet analysis: %s", analysis_id)
                return result.data[0]
            
            logger.warning("Tweet analysis not found: %s", analysis_id)
            return None
            
        except Exception as e:
            logger.error("Failed to retrieve tweet analysis %s: %s", analysis_id, str(e))
            raise

    def get_by_campaign_and_tweet(self, campaign_id: str, tweet_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis for a specific tweet in a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            tweet_id: Twitter tweet ID
            
        Returns:
            Analysis record or None if not found
        """
        try:
            result = (
                self._db.table("tweet_analysis")
                .select("*")
                .eq("campaign_id", campaign_id)
                .eq("tweet_id", tweet_id)
                .execute()
            )
            
            if result.data and len(result.data) > 0:
                logger.info("Retrieved analysis for tweet %s in campaign %s", tweet_id, campaign_id)
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("Failed to retrieve analysis for tweet %s in campaign %s: %s", 
                        tweet_id, campaign_id, str(e))
            raise

    def list_by_campaign(self, campaign_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all analyses for a campaign, ordered by score (highest first).
        
        Args:
            campaign_id: UUID string of the campaign
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of analysis records
        """
        try:
            result = (
                self._db.table("tweet_analysis")
                .select("*")
                .eq("campaign_id", campaign_id)
                .order("average_score", desc=True)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            logger.info("Listed %d analyses for campaign %s", len(result.data), campaign_id)
            return result.data
            
        except Exception as e:
            logger.error("Failed to list analyses for campaign %s: %s", campaign_id, str(e))
            raise

    def get_top_tweets(self, campaign_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get top N tweets by score for a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            limit: Number of top tweets to return
            
        Returns:
            List of top analysis records
        """
        try:
            result = (
                self._db.table("tweet_analysis")
                .select("*")
                .eq("campaign_id", campaign_id)
                .order("average_score", desc=True)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            logger.info("Retrieved top %d tweets for campaign %s", len(result.data), campaign_id)
            return result.data
            
        except Exception as e:
            logger.error("Failed to get top tweets for campaign %s: %s", campaign_id, str(e))
            raise

    def mark_top_tweets(self, campaign_id: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Mark top N tweets as is_top_3 = TRUE for a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            top_n: Number of top tweets to mark
            
        Returns:
            List of marked analysis records
        """
        try:
            # First, unmark all tweets in the campaign
            self._db.table("tweet_analysis").update({"is_top_3": False}).eq("campaign_id", campaign_id).execute()
            
            # Get top N tweets
            top_tweets = self.get_top_tweets(campaign_id, top_n)
            
            if not top_tweets:
                logger.warning("No tweets found to mark as top for campaign %s", campaign_id)
                return []
            
            # Mark them as top 3
            top_ids = [tweet["id"] for tweet in top_tweets]
            result = (
                self._db.table("tweet_analysis")
                .update({"is_top_3": True, "updated_at": "now()"})
                .in_("id", top_ids)
                .execute()
            )
            
            logger.info("Marked %d tweets as top 3 for campaign %s", len(result.data), campaign_id)
            return result.data
            
        except Exception as e:
            logger.error("Failed to mark top tweets for campaign %s: %s", campaign_id, str(e))
            raise

    def get_top_3_tweets(self, campaign_id: str) -> List[Dict[str, Any]]:
        """
        Get tweets marked as top 3 for a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            
        Returns:
            List of top 3 analysis records
        """
        try:
            result = (
                self._db.table("tweet_analysis")
                .select("*")
                .eq("campaign_id", campaign_id)
                .eq("is_top_3", True)
                .order("average_score", desc=True)
                .execute()
            )
            
            logger.info("Retrieved %d top 3 tweets for campaign %s", len(result.data), campaign_id)
            return result.data
            
        except Exception as e:
            logger.error("Failed to get top 3 tweets for campaign %s: %s", campaign_id, str(e))
            raise

    def count_by_campaign(self, campaign_id: str) -> int:
        """
        Count total analyses for a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            
        Returns:
            Total count of analyses
        """
        try:
            result = (
                self._db.table("tweet_analysis")
                .select("id", count="exact")
                .eq("campaign_id", campaign_id)
                .execute()
            )
            
            count = result.count or 0
            logger.info("Campaign %s has %d analyses", campaign_id, count)
            return count
            
        except Exception as e:
            logger.error("Failed to count analyses for campaign %s: %s", campaign_id, str(e))
            raise

    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get analysis statistics for a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Get all analyses for the campaign
            analyses = self.list_by_campaign(campaign_id, limit=1000)
            
            if not analyses:
                return {
                    "total_tweets": 0,
                    "approved_tweets": 0,
                    "rejected_tweets": 0,
                    "average_score": 0.0,
                    "top_3_count": 0
                }
            
            total = len(analyses)
            approved = len([a for a in analyses if a["verdict"] == "APPROVED"])
            rejected = total - approved
            avg_score = sum(a["average_score"] for a in analyses) / total
            top_3_count = len([a for a in analyses if a["is_top_3"]])
            
            stats = {
                "total_tweets": total,
                "approved_tweets": approved,
                "rejected_tweets": rejected,
                "average_score": round(avg_score, 1),
                "top_3_count": top_3_count
            }
            
            logger.info("Campaign %s stats: %s", campaign_id, stats)
            return stats
            
        except Exception as e:
            logger.error("Failed to get stats for campaign %s: %s", campaign_id, str(e))
            raise

    def delete_by_campaign(self, campaign_id: str) -> int:
        """
        Delete all analyses for a campaign.
        
        Args:
            campaign_id: UUID string of the campaign
            
        Returns:
            Number of deleted records
        """
        try:
            result = self._db.table("tweet_analysis").delete().eq("campaign_id", campaign_id).execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info("Deleted %d analyses for campaign %s", deleted_count, campaign_id)
            return deleted_count
            
        except Exception as e:
            logger.error("Failed to delete analyses for campaign %s: %s", campaign_id, str(e))
            raise