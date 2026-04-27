"""
Assistant Service — orchestrates assistant retrieval and management.

Handles business logic for assistant operations.
"""

from typing import List

from fastapi import HTTPException, status

from src.models.assistant import (
    Assistant,
    AssistantUpdateDTO,
)
from src.repositories.assistant_repository import AssistantRepository
from src.core.logging_config import get_logger

logger = get_logger("services.assistant_service")


class AssistantService:
    """Business logic for assistant management."""

    def __init__(self, repo: AssistantRepository) -> None:
        self._repo = repo

    # ─── Read ────────────────────────────────────────────────────────────────

    def list_assistants(self) -> List[Assistant]:
        """
        List all 3 assistants.
        
        Returns:
            List of all assistants ordered by role
        """
        try:
            records = self._repo.list_all()
            return [Assistant(**r) for r in records]
        except Exception as e:
            logger.error("Failed to list assistants: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list assistants",
            )

    def get_assistant(self, assistant_id: str) -> Assistant:
        """
        Get assistant by ID.
        
        Args:
            assistant_id: UUID string of the assistant
            
        Returns:
            Assistant object
            
        Raises:
            HTTPException: If assistant not found
        """
        try:
            record = self._repo.get_by_id(assistant_id)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assistant {assistant_id} not found",
                )
            return Assistant(**record)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get assistant %s: %s", assistant_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve assistant",
            )

    def get_assistant_by_role(self, role: str) -> Assistant:
        """
        Get assistant by role (search, comment, review).
        
        Args:
            role: Assistant role
            
        Returns:
            Assistant object
            
        Raises:
            HTTPException: If assistant not found
        """
        try:
            record = self._repo.get_by_role(role)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assistant with role '{role}' not found",
                )
            return Assistant(**record)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get assistant by role %s: %s", role, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve assistant",
            )

    # ─── Update ──────────────────────────────────────────────────────────────

    def update_assistant(self, assistant_id: str, data: AssistantUpdateDTO) -> Assistant:
        """
        Update an assistant.
        
        Args:
            assistant_id: UUID string of the assistant
            data: Update data
            
        Returns:
            Updated assistant
            
        Raises:
            HTTPException: If assistant not found or update fails
        """
        try:
            # Verify assistant exists
            self.get_assistant(assistant_id)

            # Convert DTO to dict, excluding None values
            update_data = {}
            for field, value in data.model_dump().items():
                if value is not None:
                    update_data[field] = value

            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update",
                )

            updated = self._repo.update(assistant_id, update_data)
            logger.info("Assistant %s updated", assistant_id)
            
            return Assistant(**updated)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to update assistant %s: %s", assistant_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update assistant",
            )
