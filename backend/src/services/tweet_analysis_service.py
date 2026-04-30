"""Tweet analysis service using OpenAI for scoring tweets with 5 criteria"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import OpenAI
from src.models.tweet_analysis import (
    TweetAnalysisResult,
    TweetAnalysisScores,
    TweetAnalysisCreateDTO,
    TweetAnalysis,
)
from src.models.campaign import Tweet
from src.repositories.tweet_analysis_repository import TweetAnalysisRepository
from src.core.logging_config import get_logger
from src.core.config import settings
from src.utils.openai_utils import (
    retry_with_exponential_backoff,
    OpenAIRateLimiter,
    OpenAICostTracker,
    get_global_rate_limiter,
    get_global_cost_tracker,
)

logger = get_logger("services.tweet_analysis_service")


class TweetAnalysisService:
    """Service for analyzing tweets using OpenAI with 5 scoring criteria."""

    def __init__(
        self,
        openai_client: OpenAI,
        repo: TweetAnalysisRepository,
        rate_limiter: Optional[OpenAIRateLimiter] = None,
        cost_tracker: Optional[OpenAICostTracker] = None,
    ):
        self._client = openai_client
        self._repo = repo
        self._rate_limiter = rate_limiter or get_global_rate_limiter()
        self._cost_tracker = cost_tracker or get_global_cost_tracker()

    async def analyze_tweet(self, tweet: Tweet, campaign_id: str) -> TweetAnalysis:
        """
        Analyze a single tweet using OpenAI with retry logic and rate limiting.

        Args:
            tweet: Tweet object to analyze
            campaign_id: UUID string of the campaign

        Returns:
            TweetAnalysis object with scores and verdict

        Raises:
            Exception: If analysis fails after max attempts
        """
        try:
            # Check if analysis already exists
            existing = self._repo.get_by_campaign_and_tweet(campaign_id, tweet.id)
            if existing:
                logger.info("Analysis already exists for tweet %s", tweet.id)
                return TweetAnalysis(**existing)

            # Build analysis prompt
            prompt = self._build_analysis_prompt(tweet)

            # Call OpenAI with retry logic and rate limiting
            logger.info("Analyzing tweet %s with OpenAI", tweet.id)

            async def make_openai_call():
                # Apply rate limiting
                await self._rate_limiter.acquire()

                # Make API call
                response = self._client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=1000,
                )

                # Track costs
                if hasattr(response, "usage"):
                    await self._cost_tracker.record_usage(
                        response.usage.prompt_tokens, response.usage.completion_tokens
                    )

                return response

            response = await retry_with_exponential_backoff(make_openai_call, max_retries=3)

            # Parse response
            content = response.choices[0].message.content
            analysis_data = json.loads(content)

            # Create analysis result
            scores = TweetAnalysisScores(**analysis_data["scores"])
            result = TweetAnalysisResult(scores=scores, notes=analysis_data["notes"])

            # Create DTO for database
            create_dto = TweetAnalysisCreateDTO(
                campaign_id=campaign_id, tweet_id=tweet.id, scores=scores, notes=result.notes
            )

            # Save to database
            db_record = self._repo.create(create_dto.to_db_dict())

            logger.info(
                "Tweet %s analyzed: avg=%.1f, verdict=%s",
                tweet.id,
                result.calculate_average(),
                result.get_verdict().value,
            )

            return TweetAnalysis(**db_record)

        except Exception as e:
            logger.error("Failed to analyze tweet %s: %s", tweet.id, str(e))
            raise

    async def analyze_tweets_batch(
        self, tweets: List[Tweet], campaign_id: str, max_concurrent: int = 5
    ) -> List[TweetAnalysis]:
        """
        Analyze multiple tweets in parallel.

        Args:
            tweets: List of Tweet objects to analyze
            campaign_id: UUID string of the campaign
            max_concurrent: Maximum concurrent OpenAI requests

        Returns:
            List of TweetAnalysis objects
        """
        if not tweets:
            return []

        logger.info("Starting batch analysis of %d tweets", len(tweets))

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(tweet: Tweet) -> TweetAnalysis:
            async with semaphore:
                return await self.analyze_tweet(tweet, campaign_id)

        # Run analyses in parallel
        tasks = [analyze_with_semaphore(tweet) for tweet in tweets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        analyses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Failed to analyze tweet %s: %s", tweets[i].id, str(result))
            else:
                analyses.append(result)

        logger.info("Completed batch analysis: %d/%d successful", len(analyses), len(tweets))
        return analyses

    def mark_top_tweets(self, campaign_id: str, top_n: int = 3) -> List[TweetAnalysis]:
        """
        Mark top N tweets by score for a campaign.

        Args:
            campaign_id: UUID string of the campaign
            top_n: Number of top tweets to mark

        Returns:
            List of top TweetAnalysis objects
        """
        try:
            marked_records = self._repo.mark_top_tweets(campaign_id, top_n)
            analyses = [TweetAnalysis(**record) for record in marked_records]

            logger.info("Marked %d top tweets for campaign %s", len(analyses), campaign_id)
            return analyses

        except Exception as e:
            logger.error("Failed to mark top tweets for campaign %s: %s", campaign_id, str(e))
            raise

    def get_campaign_analyses(self, campaign_id: str) -> List[TweetAnalysis]:
        """
        Get all analyses for a campaign.

        Args:
            campaign_id: UUID string of the campaign

        Returns:
            List of TweetAnalysis objects ordered by score
        """
        try:
            records = self._repo.list_by_campaign(campaign_id)
            analyses = [TweetAnalysis(**record) for record in records]

            logger.info("Retrieved %d analyses for campaign %s", len(analyses), campaign_id)
            return analyses

        except Exception as e:
            logger.error("Failed to get analyses for campaign %s: %s", campaign_id, str(e))
            raise

    def get_top_3_tweets(self, campaign_id: str) -> List[TweetAnalysis]:
        """
        Get tweets marked as top 3 for a campaign.

        Args:
            campaign_id: UUID string of the campaign

        Returns:
            List of top 3 TweetAnalysis objects
        """
        try:
            records = self._repo.get_top_3_tweets(campaign_id)
            analyses = [TweetAnalysis(**record) for record in records]

            logger.info("Retrieved %d top 3 tweets for campaign %s", len(analyses), campaign_id)
            return analyses

        except Exception as e:
            logger.error("Failed to get top 3 tweets for campaign %s: %s", campaign_id, str(e))
            raise

    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get analysis statistics for a campaign.

        Args:
            campaign_id: UUID string of the campaign

        Returns:
            Dictionary with analysis statistics
        """
        try:
            stats = self._repo.get_campaign_stats(campaign_id)
            logger.info("Retrieved stats for campaign %s: %s", campaign_id, stats)
            return stats

        except Exception as e:
            logger.error("Failed to get stats for campaign %s: %s", campaign_id, str(e))
            raise

    def get_cost_stats(self) -> Dict[str, Any]:
        """
        Get OpenAI API cost statistics.

        Returns:
            Dictionary with cost statistics
        """
        return self._cost_tracker.get_stats()

    def _build_analysis_prompt(self, tweet: Tweet) -> str:
        """
        Build the analysis prompt for OpenAI.

        Args:
            tweet: Tweet object to analyze

        Returns:
            Formatted prompt string
        """
        return f"""
Analyze this tweet and provide scores for each criterion:

TWEET DETAILS:
Author: @{tweet.author}
Text: "{tweet.text}"
Engagement: {tweet.likes} likes, {tweet.reposts} retweets, {tweet.replies} replies
URL: {tweet.url}

SCORING CRITERIA (0-10 scale):

1. LEAD RELEVANCE (0-10): Is the author a relevant decision-maker?
   - 9-10: C-level executive, founder, or senior decision-maker at a company
   - 7-8: Manager, director, or team lead with decision-making authority
   - 5-6: Professional with some influence but limited decision-making power
   - 3-4: Individual contributor or junior professional
   - 0-2: Student, personal account, or unclear professional status

2. TONE OF VOICE (0-10): Is the tone professional and consultative?
   - 9-10: Highly professional, thoughtful, consultative approach
   - 7-8: Professional with good insights, appropriate business tone
   - 5-6: Somewhat professional but may lack depth or polish
   - 3-4: Casual or unprofessional tone, limited business value
   - 0-2: Inappropriate, aggressive, or completely unprofessional

3. INSIGHT STRENGTH (0-10): Does the tweet provide valuable business insights?
   - 9-10: Exceptional insights, strategic thinking, valuable perspectives
   - 7-8: Good insights with practical value for business decisions
   - 5-6: Some useful information but limited depth or originality
   - 3-4: Basic observations with minimal business value
   - 0-2: No meaningful insights or purely personal content

4. ENGAGEMENT POTENTIAL (0-10): Does it invite meaningful business conversation?
   - 9-10: Highly engaging, invites strategic discussion and collaboration
   - 7-8: Good conversation starter with clear business relevance
   - 5-6: Moderately engaging but may lack clear discussion points
   - 3-4: Limited engagement potential, unclear conversation direction
   - 0-2: No engagement potential or inappropriate for business discussion

5. BRAND SAFETY (0-10): Is it safe for professional brand engagement?
   - 9-10: Completely safe, aligns with professional values and standards
   - 7-8: Generally safe with minor considerations
   - 5-6: Mostly safe but requires careful response approach
   - 3-4: Some risk factors, controversial topics, or sensitive content
   - 0-2: High risk, inappropriate content, or potential brand damage

Provide your analysis in this exact JSON format:
{{
    "scores": {{
        "lead_relevance": <score>,
        "tone_of_voice": <score>,
        "insight_strength": <score>,
        "engagement_potential": <score>,
        "brand_safety": <score>
    }},
    "notes": "<brief explanation of the scores and overall assessment>"
}}
"""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for tweet analysis."""
        return """You are Rita, an expert analyst for Growth Collective, a marketing agency specializing in DTC brands. Your job is to analyze tweets from potential clients and prospects to determine their value for business engagement.

You evaluate tweets based on 5 criteria, each scored 0-10:
1. Lead Relevance - Is the author a decision-maker worth engaging?
2. Tone of Voice - Is the communication professional and consultative?
3. Insight Strength - Does the tweet provide valuable business insights?
4. Engagement Potential - Does it invite meaningful business conversation?
5. Brand Safety - Is it safe for professional brand engagement?

Be objective and consistent in your scoring. Consider the business context and potential for meaningful professional relationships. Your analysis helps determine which tweets deserve strategic engagement from Growth Collective.

Always respond with valid JSON in the exact format requested."""
