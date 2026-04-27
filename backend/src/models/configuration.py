"""Configuration data models"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class ConfigurationDTO(BaseModel):
    """Configuration data transfer object"""

    user_email: EmailStr
    apify_token: str
    openai_token: str
    smtp_password: str
    twitter_auth_token: Optional[str] = None
    twitter_ct0: Optional[str] = None


class ConfigurationResponseDTO(BaseModel):
    """Configuration response with masked tokens"""

    user_email: EmailStr
    apify_token_masked: str
    openai_token_masked: str
    smtp_password_masked: str
    twitter_auth_token_present: bool
    twitter_ct0_present: bool
