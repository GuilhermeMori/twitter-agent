"""Assistant repository for database operations"""

from typing import List, Optional, Dict, Any
from supabase import Client
from src.core.logging_config import get_logger

logger = get_logger("repositories.assistant_repository")


class AssistantRepository:
    """Repository for assistant database operations."""

    def __init__(self, db: Client) -> None:
        self._db = db

    def list_all(self) -> List[Dict[str, Any]]:
        """
        List all assistants (always 3).

        Returns:
            List of assistant records ordered by role
        """
        try:
            result = (
                self._db.table("assistants")
                .select("*")
                .order("role")  # search, comment, review
                .execute()
            )

            logger.info("Listed %d assistants", len(result.data))
            return result.data

        except Exception as e:
            logger.error("Failed to list assistants: %s", str(e))
            raise

    def get_by_id(self, assistant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get assistant by ID.

        Args:
            assistant_id: UUID string of the assistant

        Returns:
            Assistant record or None if not found
        """
        try:
            result = self._db.table("assistants").select("*").eq("id", assistant_id).execute()

            if result.data and len(result.data) > 0:
                logger.info("Retrieved assistant: %s", assistant_id)
                return result.data[0]

            logger.warning("Assistant not found: %s", assistant_id)
            return None

        except Exception as e:
            logger.error("Failed to get assistant %s: %s", assistant_id, str(e))
            raise

    def get_by_role(self, role: str) -> Optional[Dict[str, Any]]:
        """
        Get assistant by role.

        Args:
            role: Assistant role (search, comment, review)

        Returns:
            Assistant record or None if not found
        """
        try:
            result = self._db.table("assistants").select("*").eq("role", role).limit(1).execute()

            if result.data and len(result.data) > 0:
                logger.info("Retrieved assistant by role: %s", role)
                return result.data[0]

            logger.warning("Assistant not found for role: %s", role)
            return None

        except Exception as e:
            logger.error("Failed to get assistant by role %s: %s", role, str(e))
            raise

    def update(self, assistant_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an assistant.

        Args:
            assistant_id: UUID string of the assistant
            update_data: Dictionary with fields to update

        Returns:
            Updated assistant record

        Raises:
            Exception: If assistant not found or update fails
        """
        try:
            # Add updated_at timestamp
            update_data["updated_at"] = "now()"

            result = (
                self._db.table("assistants").update(update_data).eq("id", assistant_id).execute()
            )

            if not result.data:
                raise Exception(f"Assistant {assistant_id} not found")

            logger.info("Updated assistant: %s", assistant_id)
            return result.data[0]

        except Exception as e:
            logger.error("Failed to update assistant %s: %s", assistant_id, str(e))
            raise
