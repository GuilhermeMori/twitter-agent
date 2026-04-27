"""Assistant data models"""

from pydantic import BaseModel, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID


# ─── Input DTOs ──────────────────────────────────────────────────────────────

class AssistantUpdateDTO(BaseModel):
    """Assistant update data transfer object."""

    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    principles: Optional[List[str]] = None
    quality_criteria: Optional[List[str]] = None
    skills: Optional[List[str]] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Assistant name cannot be empty")
        return v.strip() if v else v

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Assistant title cannot be empty")
        return v.strip() if v else v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Assistant description cannot be empty")
        return v.strip() if v else v

    @field_validator("instructions")
    @classmethod
    def instructions_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Assistant instructions cannot be empty")
        return v.strip() if v else v

    @field_validator("principles")
    @classmethod
    def principles_valid(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            if len(v) == 0:
                raise ValueError("At least one principle is required")
            # Remove empty strings and strip whitespace
            cleaned = [p.strip() for p in v if p and p.strip()]
            if not cleaned:
                raise ValueError("At least one non-empty principle is required")
            return cleaned
        return v

    @field_validator("quality_criteria")
    @classmethod
    def quality_criteria_valid(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            # Remove empty strings and strip whitespace
            cleaned = [c.strip() for c in v if c and c.strip()]
            return cleaned
        return v

    @field_validator("skills")
    @classmethod
    def skills_valid(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            # Remove empty strings and strip whitespace
            cleaned = [s.strip() for s in v if s and s.strip()]
            return cleaned
        return v


# ─── Domain models ───────────────────────────────────────────────────────────

class Assistant(BaseModel):
    """Full assistant record returned from the database."""

    id: UUID
    name: str
    title: str
    role: Literal['search', 'comment', 'review']
    description: str
    instructions: str
    principles: List[str]
    quality_criteria: List[str]
    skills: List[str]
    is_editable: bool
    created_at: datetime
    updated_at: datetime


class AssistantSummary(BaseModel):
    """Simplified assistant for lists and dropdowns."""

    id: UUID
    name: str
    title: str
    role: Literal['search', 'comment', 'review']
    is_editable: bool
    created_at: datetime
