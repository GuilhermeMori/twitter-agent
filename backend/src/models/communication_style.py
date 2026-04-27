"""Communication Style data models"""

from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ─── Input DTOs ──────────────────────────────────────────────────────────────

class CommunicationStyleCreateDTO(BaseModel):
    """Communication style creation data transfer object — validated on receipt."""

    name: str
    title: str
    description: str
    tone_of_voice: str
    principles: List[str]
    vocabulary_allowed: Optional[List[str]] = None
    vocabulary_prohibited: Optional[List[str]] = None
    formatting_rules: Optional[List[str]] = None
    language: str = "en"
    system_prompt: str = ""
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Communication style name cannot be empty")
        return v.strip()

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Communication style title cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Communication style description cannot be empty")
        return v.strip()

    @field_validator("tone_of_voice")
    @classmethod
    def tone_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tone of voice cannot be empty")
        return v.strip()

    @field_validator("principles")
    @classmethod
    def principles_not_empty(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError("At least one principle is required")
        # Remove empty strings and strip whitespace
        cleaned = [p.strip() for p in v if p and p.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty principle is required")
        return cleaned

    @field_validator("language")
    @classmethod
    def language_valid(cls, v: str) -> str:
        valid_languages = ["en", "pt", "es", "fr", "de", "it"]
        if v not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v


class CommunicationStyleUpdateDTO(BaseModel):
    """Communication style update data transfer object."""

    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tone_of_voice: Optional[str] = None
    principles: Optional[List[str]] = None
    vocabulary_allowed: Optional[List[str]] = None
    vocabulary_prohibited: Optional[List[str]] = None
    formatting_rules: Optional[List[str]] = None
    language: Optional[str] = None
    system_prompt: Optional[str] = None
    is_default: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Communication style name cannot be empty")
        return v.strip() if v else v

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Communication style title cannot be empty")
        return v.strip() if v else v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Communication style description cannot be empty")
        return v.strip() if v else v

    @field_validator("tone_of_voice")
    @classmethod
    def tone_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Tone of voice cannot be empty")
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

    @field_validator("language")
    @classmethod
    def language_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_languages = ["en", "pt", "es", "fr", "de", "it"]
            if v not in valid_languages:
                raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v


# ─── Domain models ───────────────────────────────────────────────────────────

class CommunicationStyle(BaseModel):
    """Full communication style record returned from the database."""

    id: UUID
    name: str
    title: str
    description: str
    tone_of_voice: str
    principles: List[str]
    vocabulary_allowed: Optional[List[str]] = None
    vocabulary_prohibited: Optional[List[str]] = None
    formatting_rules: Optional[List[str]] = None
    language: str
    system_prompt: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class CommunicationStyleSummary(BaseModel):
    """Simplified communication style for lists and dropdowns."""

    id: UUID
    name: str
    title: str
    language: str
    is_default: bool
    created_at: datetime