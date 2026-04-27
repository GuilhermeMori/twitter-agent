"""Tweet analysis data models"""

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class Verdict(str, Enum):
    """Analysis verdict enumeration."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TweetAnalysisScores(BaseModel):
    """Individual scoring criteria for tweet analysis."""
    
    lead_relevance: int
    tone_of_voice: int
    insight_strength: int
    engagement_potential: int
    brand_safety: int

    @field_validator("lead_relevance", "tone_of_voice", "insight_strength", 
                     "engagement_potential", "brand_safety")
    @classmethod
    def score_range(cls, v: int) -> int:
        if not 0 <= v <= 10:
            raise ValueError("Score must be between 0 and 10")
        return v

    def calculate_average(self) -> float:
        """Calculate average score from all criteria."""
        total = (
            self.lead_relevance +
            self.tone_of_voice +
            self.insight_strength +
            self.engagement_potential +
            self.brand_safety
        )
        return round(total / 5, 1)


class TweetAnalysisResult(BaseModel):
    """Analysis result from OpenAI API."""
    
    scores: TweetAnalysisScores
    notes: str
    
    def calculate_average(self) -> float:
        """Calculate average score."""
        return self.scores.calculate_average()
    
    def get_verdict(self) -> Verdict:
        """Determine verdict based on average score."""
        return Verdict.APPROVED if self.calculate_average() >= 8.0 else Verdict.REJECTED


class TweetAnalysis(BaseModel):
    """Complete tweet analysis record from database."""
    
    id: UUID
    campaign_id: UUID
    tweet_id: str
    lead_relevance_score: int
    tone_of_voice_score: int
    insight_strength_score: int
    engagement_potential_score: int
    brand_safety_score: int
    average_score: float
    verdict: Verdict
    notes: Optional[str] = None
    is_top_3: bool = False
    created_at: datetime
    updated_at: datetime

    @property
    def scores(self) -> TweetAnalysisScores:
        """Get scores as TweetAnalysisScores object."""
        return TweetAnalysisScores(
            lead_relevance=self.lead_relevance_score,
            tone_of_voice=self.tone_of_voice_score,
            insight_strength=self.insight_strength_score,
            engagement_potential=self.engagement_potential_score,
            brand_safety=self.brand_safety_score
        )


class TweetAnalysisCreateDTO(BaseModel):
    """Data transfer object for creating tweet analysis."""
    
    campaign_id: UUID
    tweet_id: str
    scores: TweetAnalysisScores
    notes: str
    
    def to_db_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        average = self.scores.calculate_average()
        verdict = Verdict.APPROVED if average >= 8.0 else Verdict.REJECTED
        
        return {
            "campaign_id": str(self.campaign_id),
            "tweet_id": self.tweet_id,
            "lead_relevance_score": self.scores.lead_relevance,
            "tone_of_voice_score": self.scores.tone_of_voice,
            "insight_strength_score": self.scores.insight_strength,
            "engagement_potential_score": self.scores.engagement_potential,
            "brand_safety_score": self.scores.brand_safety,
            "average_score": average,
            "verdict": verdict.value,
            "notes": self.notes,
            "is_top_3": False
        }


class TweetAnalysisSummary(BaseModel):
    """Summary of tweet analysis for lists and overviews."""
    
    id: UUID
    tweet_id: str
    average_score: float
    verdict: Verdict
    is_top_3: bool
    created_at: datetime