"""Tweet comment data models"""

from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class ValidationStatus(str, Enum):
    """Comment validation status enumeration."""
    VALID = "valid"
    FAILED = "failed"
    REGENERATED = "regenerated"


class CommentGenerationRequest(BaseModel):
    """Request to generate a comment for a tweet."""
    
    tweet_text: str
    tweet_author: str
    tweet_url: str
    persona_id: UUID
    campaign_id: UUID

    @field_validator("tweet_text", "tweet_author", "tweet_url")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class CommentValidationResult(BaseModel):
    """Result of comment validation."""
    
    is_valid: bool
    errors: List[str] = []
    char_count: int

    @classmethod
    def valid(cls, char_count: int) -> "CommentValidationResult":
        """Create a valid result."""
        return cls(is_valid=True, errors=[], char_count=char_count)

    @classmethod
    def invalid(cls, errors: List[str], char_count: int) -> "CommentValidationResult":
        """Create an invalid result with errors."""
        return cls(is_valid=False, errors=errors, char_count=char_count)


class TweetComment(BaseModel):
    """Tweet comment record from database."""
    
    id: UUID
    campaign_id: UUID
    tweet_id: str
    persona_id: UUID
    comment_text: str
    char_count: int
    generation_attempt: int
    validation_status: ValidationStatus
    validation_errors: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("char_count")
    @classmethod
    def char_count_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Character count must be positive")
        return v

    @field_validator("generation_attempt")
    @classmethod
    def attempt_valid(cls, v: int) -> int:
        if not 1 <= v <= 3:
            raise ValueError("Generation attempt must be between 1 and 3")
        return v


class TweetCommentCreateDTO(BaseModel):
    """Data transfer object for creating tweet comment."""
    
    campaign_id: UUID
    tweet_id: str
    persona_id: UUID
    comment_text: str
    generation_attempt: int = 1
    validation_result: CommentValidationResult

    def to_db_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        return {
            "campaign_id": str(self.campaign_id),
            "tweet_id": self.tweet_id,
            "persona_id": str(self.persona_id),
            "comment_text": self.comment_text,
            "char_count": self.validation_result.char_count,
            "generation_attempt": self.generation_attempt,
            "validation_status": ValidationStatus.VALID.value if self.validation_result.is_valid else ValidationStatus.FAILED.value,
            "validation_errors": self.validation_result.errors if not self.validation_result.is_valid else None
        }


class TweetCommentSummary(BaseModel):
    """Summary of tweet comment for lists."""
    
    id: UUID
    tweet_id: str
    comment_text: str
    char_count: int
    validation_status: ValidationStatus
    created_at: datetime


class CommentRegenerationRequest(BaseModel):
    """Request to regenerate a comment."""
    
    campaign_id: UUID
    tweet_id: str
    persona_id: Optional[UUID] = None  # If None, use original persona

    @field_validator("tweet_id")
    @classmethod
    def tweet_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tweet ID cannot be empty")
        return v.strip()