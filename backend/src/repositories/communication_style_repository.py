"""Communication Style repository for database operations"""

from typing import List, Optional, Dict, Any
from supabase import Client
from src.core.logging_config import get_logger

logger = get_logger("repositories.communication_style_repository")


class CommunicationStyleRepository:
    """Repository for communication style database operations."""

    def __init__(self, db: Client) -> None:
        self._db = db

    def create(self, communication_style_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new communication style in the database.
        
        Args:
            communication_style_data: Dictionary with communication style fields
            
        Returns:
            Created communication style record
            
        Raises:
            Exception: If database operation fails
        """
        try:
            # If this communication style is being set as default, unset all other defaults first
            if communication_style_data.get("is_default", False):
                self._unset_all_defaults()
            
            result = self._db.table("communication_styles").insert(communication_style_data).execute()
            
            if not result.data:
                raise Exception("Failed to create communication style")
                
            logger.info("Created communication style: %s", result.data[0]["id"])
            return result.data[0]
            
        except Exception as e:
            logger.error("Failed to create communication style: %s", str(e))
            raise

    def get_by_id(self, communication_style_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a communication style by ID.
        
        Args:
            communication_style_id: UUID string of the communication style
            
        Returns:
            Communication style record or None if not found
        """
        try:
            result = self._db.table("communication_styles").select("*").eq("id", communication_style_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.info("Retrieved communication style: %s", communication_style_id)
                return result.data[0]
            
            logger.warning("Communication style not found: %s", communication_style_id)
            return None
            
        except Exception as e:
            logger.error("Failed to retrieve communication style %s: %s", communication_style_id, str(e))
            raise

    def list_all(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all communication styles with pagination.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of communication style records
        """
        try:
            result = (
                self._db.table("communication_styles")
                .select("*")
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            logger.info("Listed %d communication styles", len(result.data))
            return result.data
            
        except Exception as e:
            logger.error("Failed to list communication styles: %s", str(e))
            raise

    def list_summaries(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List communication style summaries (for dropdowns and lists).
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of communication style summary records
        """
        try:
            result = (
                self._db.table("communication_styles")
                .select("id, name, title, language, is_default, created_at")
                .order("is_default", desc=True)  # Default communication styles first
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            logger.info("Listed %d communication style summaries", len(result.data))
            return result.data
            
        except Exception as e:
            logger.error("Failed to list communication style summaries: %s", str(e))
            raise

    def update(self, communication_style_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a communication style.
        
        Args:
            communication_style_id: UUID string of the communication style
            update_data: Dictionary with fields to update
            
        Returns:
            Updated communication style record
            
        Raises:
            Exception: If communication style not found or update fails
        """
        try:
            # If setting this communication style as default, unset all other defaults first
            if update_data.get("is_default", False):
                self._unset_all_defaults()
            
            # Add updated_at timestamp
            update_data["updated_at"] = "now()"
            
            result = (
                self._db.table("communication_styles")
                .update(update_data)
                .eq("id", communication_style_id)
                .execute()
            )
            
            if not result.data:
                raise Exception(f"Communication style {communication_style_id} not found")
                
            logger.info("Updated communication style: %s", communication_style_id)
            return result.data[0]
            
        except Exception as e:
            logger.error("Failed to update communication style %s: %s", communication_style_id, str(e))
            raise

    def delete(self, communication_style_id: str) -> bool:
        """
        Delete a communication style.
        
        Args:
            communication_style_id: UUID string of the communication style
            
        Returns:
            True if deleted successfully
            
        Raises:
            Exception: If communication style not found or delete fails
        """
        try:
            result = self._db.table("communication_styles").delete().eq("id", communication_style_id).execute()
            
            if not result.data:
                raise Exception(f"Communication style {communication_style_id} not found")
                
            logger.info("Deleted communication style: %s", communication_style_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete communication style %s: %s", communication_style_id, str(e))
            raise

    def count_all(self) -> int:
        """
        Count total number of communication styles.
        
        Returns:
            Total count of communication styles
        """
        try:
            result = (
                self._db.table("communication_styles")
                .select("id", count="exact")
                .execute()
            )
            
            count = result.count or 0
            logger.info("Total communication styles count: %d", count)
            return count
            
        except Exception as e:
            logger.error("Failed to count communication styles: %s", str(e))
            raise

    def get_default(self) -> Optional[Dict[str, Any]]:
        """
        Get the default communication style.
        
        Returns:
            Default communication style record or None if no default set
        """
        try:
            result = (
                self._db.table("communication_styles")
                .select("*")
                .eq("is_default", True)
                .limit(1)
                .execute()
            )
            
            if result.data and len(result.data) > 0:
                logger.info("Retrieved default communication style: %s", result.data[0]["id"])
                return result.data[0]
            
            logger.warning("No default communication style found")
            return None
            
        except Exception as e:
            logger.error("Failed to get default communication style: %s", str(e))
            raise

    def check_usage_in_campaigns(self, communication_style_id: str) -> List[Dict[str, Any]]:
        """
        Check if communication style is used in any campaigns.
        
        Args:
            communication_style_id: UUID string of the communication style
            
        Returns:
            List of campaigns using this communication style
        """
        try:
            result = (
                self._db.table("campaigns")
                .select("id, name, status, created_at")
                .eq("communication_style_id", communication_style_id)
                .execute()
            )
            
            logger.info("Found %d campaigns using communication style %s", len(result.data), communication_style_id)
            return result.data
            
        except Exception as e:
            logger.error("Failed to check communication style usage %s: %s", communication_style_id, str(e))
            raise

    def _unset_all_defaults(self) -> None:
        """
        Unset is_default flag for all communication styles.
        Internal helper method.
        """
        try:
            self._db.table("communication_styles").update({"is_default": False}).eq("is_default", True).execute()
            logger.info("Unset all default communication styles")
            
        except Exception as e:
            logger.error("Failed to unset default communication styles: %s", str(e))
            raise