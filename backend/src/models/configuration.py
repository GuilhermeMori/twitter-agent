"""Configuration data models"""

from pydantic import BaseModel
from typing import Optional


class ConfigurationDTO(BaseModel):
    """Configuration data transfer object"""

    apify_token: str
    openai_token: str
    twitter_auth_token: Optional[str] = None
    twitter_ct0: Optional[str] = None


class ConfigurationResponseDTO(BaseModel):
    """Configuration response with masked tokens"""

    apify_token_masked: str
    openai_token_masked: str
    twitter_auth_token_present: bool
    twitter_ct0_present: bool
