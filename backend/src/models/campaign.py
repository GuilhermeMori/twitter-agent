"""Campaign data models"""

from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from uuid import UUID
from enum import Enum


class SearchType(str, Enum):
    """Search type enumeration"""

    PROFILE = "profile"
    KEYWORDS = "keywords"


class CampaignStatus(str, Enum):
    """Campaign status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Input DTOs ──────────────────────────────────────────────────────────────

class CampaignCreateDTO(BaseModel):
    """Campaign creation data transfer object — validated on receipt."""

    name: str
    social_network: str = "twitter"
    search_type: SearchType
    profiles: Optional[str] = None   # Comma- or newline-separated @handles
    keywords: Optional[str] = None   # Comma- or newline-separated terms
    language: str = "en"
    min_likes: int = 0
    min_retweets: int = 0
    min_replies: int = 0
    days_back: int = 1  # Changed from hours_back to days_back
    persona_id: Optional[str] = None  # UUID of the persona to use (legacy, maps to communication_style_id)
    communication_style_id: Optional[str] = None  # UUID of the communication style to use

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Campaign name cannot be empty")
        return v.strip()

    @field_validator("min_likes", "min_retweets", "min_replies")
    @classmethod
    def engagement_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Engagement filters must be non-negative")
        return v

    @field_validator("days_back")
    @classmethod
    def days_back_valid(cls, v: int) -> int:
        if v < 1 or v > 365:
            raise ValueError("days_back must be between 1 and 365")
        return v

    @model_validator(mode="after")
    def validate_search_fields(self) -> "CampaignCreateDTO":
        if self.search_type == SearchType.PROFILE:
            if not self.profiles or not self.profiles.strip():
                raise ValueError("Profiles are required for profile search")
        if self.search_type == SearchType.KEYWORDS:
            if not self.keywords or not self.keywords.strip():
                raise ValueError("Keywords are required for keyword search")
        return self


# ─── Domain models ───────────────────────────────────────────────────────────

class CampaignConfig(BaseModel):
    """Parsed campaign configuration stored in the DB as JSONB."""

    profiles: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    language: str
    min_likes: int
    min_retweets: int
    min_replies: int
    days_back: int = 1  # Changed from hours_back
    hours_back: Optional[int] = None  # Deprecated, kept for backward compatibility

    @model_validator(mode="after")
    def convert_hours_to_days(self) -> "CampaignConfig":
        """Convert old hours_back to days_back for backward compatibility."""
        if self.hours_back is not None and self.days_back == 1:
            # Convert hours to days (round up)
            self.days_back = max(1, (self.hours_back + 23) // 24)
        return self


class Campaign(BaseModel):
    """Full campaign record returned from the database."""

    id: UUID
    name: str
    social_network: str
    search_type: str
    config: CampaignConfig
    status: CampaignStatus
    error_message: Optional[str] = None
    document_url: Optional[str] = None
    results_count: int
    persona_id: Optional[UUID] = None  # Legacy field, maps to communication_style_id
    communication_style_id: Optional[UUID] = None  # UUID of the communication style used
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class Tweet(BaseModel):
    """Individual tweet collected during a campaign."""

    id: str
    url: str
    author: str
    text: str
    likes: int
    reposts: int
    replies: int
    timestamp: datetime


class ScrapingConfig(BaseModel):
    """Configuration passed to the scraping engine."""

    search_type: SearchType
    profiles: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    language: str = "en"
    min_likes: int = 0
    min_retweets: int = 0
    min_replies: int = 0
    days_back: int = 1  # Changed from hours_back
    apify_token: str
    twitter_auth_token: Optional[str] = None
    twitter_ct0: Optional[str] = None


# ─── Generic pagination ───────────────────────────────────────────────────────

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T]
    total: int
    page: int
    limit: int
    total_pages: int


# ─── Validation result ────────────────────────────────────────────────────────

class ValidationResult(BaseModel):
    """Result of a validation operation."""

    is_valid: bool
    errors: dict[str, str] = {}

    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(is_valid=True)

    @classmethod
    def fail(cls, field: str, message: str) -> "ValidationResult":
        return cls(is_valid=False, errors={field: message})

    @classmethod
    def fail_many(cls, errors: dict[str, str]) -> "ValidationResult":
        return cls(is_valid=False, errors=errors)
