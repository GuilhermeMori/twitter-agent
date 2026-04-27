"""Analysis data models"""

from pydantic import BaseModel
from typing import List


class Analysis(BaseModel):
    """Structured analysis produced by the OpenAI analysis engine."""

    summary: str
    key_themes: List[str]
    sentiment: str
    top_influencers: List[str]
    recommendations: List[str]
