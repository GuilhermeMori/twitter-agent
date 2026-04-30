"""Comment generation service using OpenAI, assistants, and communication styles"""

import asyncio
from typing import List, Optional
from openai import OpenAI
from src.models.tweet_comment import (
    CommentGenerationRequest,
    CommentValidationResult,
    TweetCommentCreateDTO,
    TweetComment,
    ValidationStatus,
)
from src.models.campaign import Tweet
from src.models.communication_style import CommunicationStyle
from src.models.assistant import Assistant
from src.services.communication_style_service import CommunicationStyleService
from src.services.assistant_service import AssistantService
from src.services.comment_validator import CommentValidator
from src.repositories.tweet_comment_repository import TweetCommentRepository
from src.core.logging_config import get_logger
from src.utils.openai_utils import (
    retry_with_exponential_backoff,
    OpenAIRateLimiter,
    OpenAICostTracker,
    get_global_rate_limiter,
    get_global_cost_tracker,
)

logger = get_logger("services.comment_generation_service")


class CommentGenerationService:
    """Service for generating communication style-based comments for tweets."""

    MAX_ATTEMPTS = 3
    MAX_CHARS = 350

    def __init__(
        self,
        openai_client: OpenAI,
        communication_style_service: CommunicationStyleService,
        assistant_service: AssistantService,
        repo: TweetCommentRepository,
        validator: CommentValidator,
        rate_limiter: Optional[OpenAIRateLimiter] = None,
        cost_tracker: Optional[OpenAICostTracker] = None,
    ):
        self._client = openai_client
        self._communication_style_service = communication_style_service
        self._assistant_service = assistant_service
        self._repo = repo
        self._validator = validator
        self._rate_limiter = rate_limiter or get_global_rate_limiter()
        self._cost_tracker = cost_tracker or get_global_cost_tracker()

    async def generate_comment(
        self, tweet: Tweet, communication_style_id: str, campaign_id: str
    ) -> TweetComment:
        """
        Generate a comment for a tweet using a communication style.
        """
        try:
            # Check if comment already exists
            existing = self._repo.get_by_campaign_and_tweet(campaign_id, tweet.id)
            if existing:
                logger.info("Comment already exists for tweet %s", tweet.id)
                return TweetComment(**existing)

            # Get communication style
            communication_style = self._communication_style_service.get_communication_style(
                communication_style_id
            )

            # Generate comment with retry logic
            for attempt in range(1, self.MAX_ATTEMPTS + 1):
                logger.info(
                    "Generating comment for tweet %s (attempt %d/%d)",
                    tweet.id,
                    attempt,
                    self.MAX_ATTEMPTS,
                )

                try:
                    # Generate comment text
                    comment_text = await self._generate_comment_text(tweet, communication_style)

                    # Validate comment
                    validation_result = self._validator.validate(
                        comment_text, communication_style, tweet.author
                    )

                    # Create DTO
                    create_dto = TweetCommentCreateDTO(
                        campaign_id=campaign_id,
                        tweet_id=tweet.id,
                        persona_id=communication_style_id,
                        comment_text=comment_text,
                        generation_attempt=attempt,
                        validation_result=validation_result,
                    )

                    # Save to database
                    db_record = self._repo.create(create_dto.to_db_dict())

                    if validation_result.is_valid:
                        logger.info("Successfully generated valid comment for tweet %s", tweet.id)
                        return TweetComment(**db_record)
                    else:
                        logger.warning(
                            "Generated invalid comment for tweet %s: %s",
                            tweet.id,
                            validation_result.errors,
                        )

                        # If this was the last attempt, return the failed comment
                        if attempt == self.MAX_ATTEMPTS:
                            return TweetComment(**db_record)

                except Exception as e:
                    logger.error(
                        "Error generating comment for tweet %s (attempt %d): %s",
                        tweet.id,
                        attempt,
                        str(e),
                    )

                    if attempt == self.MAX_ATTEMPTS:
                        # Create a failed comment record
                        failed_dto = TweetCommentCreateDTO(
                            campaign_id=campaign_id,
                            tweet_id=tweet.id,
                            persona_id=communication_style_id,
                            comment_text=f"@{tweet.author} [Generation failed]",
                            generation_attempt=attempt,
                            validation_result=CommentValidationResult.invalid(
                                [f"Generation error: {str(e)}"],
                                len(f"@{tweet.author} [Generation failed]"),
                            ),
                        )
                        db_record = self._repo.create(failed_dto.to_db_dict())
                        return TweetComment(**db_record)

            # This should never be reached, but just in case
            raise Exception(f"Failed to generate comment after {self.MAX_ATTEMPTS} attempts")

        except Exception as e:
            logger.error("Failed to generate comment for tweet %s: %s", tweet.id, str(e))
            raise

    async def generate_comments_batch(
        self,
        tweets: List[Tweet],
        communication_style_id: str,
        campaign_id: str,
        max_concurrent: int = 3,
    ) -> List[TweetComment]:
        """
        Generate comments for multiple tweets in parallel.
        """
        if not tweets:
            return []

        logger.info("Starting batch comment generation for %d tweets", len(tweets))

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(tweet: Tweet) -> TweetComment:
            async with semaphore:
                return await self.generate_comment(tweet, communication_style_id, campaign_id)

        # Run generation in parallel
        tasks = [generate_with_semaphore(tweet) for tweet in tweets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        comments = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Failed to generate comment for tweet %s: %s", tweets[i].id, str(result)
                )
            else:
                comments.append(result)

        logger.info(
            "Completed batch comment generation: %d/%d successful", len(comments), len(tweets)
        )
        return comments

    async def regenerate_comment(
        self, tweet: Tweet, campaign_id: str, communication_style_id: Optional[str] = None
    ) -> TweetComment:
        """
        Regenerate a comment for a tweet (user-triggered).
        """
        try:
            # Get existing comment to determine communication style if not provided
            if not communication_style_id:
                existing = self._repo.get_by_campaign_and_tweet(campaign_id, tweet.id)
                if existing:
                    communication_style_id = existing["persona_id"]
                else:
                    # Use default communication style
                    default_style = (
                        self._communication_style_service.get_default_communication_style()
                    )
                    communication_style_id = str(default_style.id)

            # Mark existing comments as regenerated
            self._repo.mark_as_regenerated(campaign_id, tweet.id)

            # Generate new comment
            logger.info(
                "Regenerating comment for tweet %s with communication style %s",
                tweet.id,
                communication_style_id,
            )
            return await self.generate_comment(tweet, communication_style_id, campaign_id)

        except Exception as e:
            logger.error("Failed to regenerate comment for tweet %s: %s", tweet.id, str(e))
            raise

    def get_campaign_comments(self, campaign_id: str) -> List[TweetComment]:
        """
        Get all valid comments for a campaign.
        """
        try:
            records = self._repo.list_by_campaign(campaign_id)
            comments = [TweetComment(**record) for record in records]

            logger.info("Retrieved %d comments for campaign %s", len(comments), campaign_id)
            return comments

        except Exception as e:
            logger.error("Failed to get comments for campaign %s: %s", campaign_id, str(e))
            raise

    def get_comments_for_tweets(self, campaign_id: str, tweet_ids: List[str]) -> List[TweetComment]:
        """
        Get comments for specific tweets in a campaign.
        """
        try:
            records = self._repo.list_by_tweet_ids(campaign_id, tweet_ids)
            comments = [TweetComment(**record) for record in records]

            logger.info(
                "Retrieved %d comments for %d tweets in campaign %s",
                len(comments),
                len(tweet_ids),
                campaign_id,
            )
            return comments

        except Exception as e:
            logger.error(
                "Failed to get comments for tweets in campaign %s: %s", campaign_id, str(e)
            )
            raise

    async def _generate_comment_text(
        self, tweet: Tweet, communication_style: CommunicationStyle
    ) -> str:
        """
        Generate comment text using OpenAI with retry logic and rate limiting.
        Combines Assistant Cadu's instructions with the communication style.
        """
        try:
            # Get Assistant Cadu (role='comment') for instructions
            try:
                assistant = self._assistant_service.get_assistant_by_role("comment")
                system_content = f"""{assistant.instructions}

---

{communication_style.system_prompt}"""
            except Exception as e:
                logger.warning("Could not fetch comment assistant, using style only: %s", str(e))
                system_content = communication_style.system_prompt

            # Build generation prompt
            prompt = self._build_generation_prompt(tweet, communication_style)

            # Call OpenAI with retry logic and rate limiting
            async def make_openai_call():
                # Apply rate limiting
                await self._rate_limiter.acquire()

                # Make API call
                response = self._client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=80,  # Reduced to enforce 280 char limit
                    presence_penalty=0.2,  # Increased to reduce repetition
                    frequency_penalty=0.2,  # Increased to encourage brevity
                )

                # Track costs
                if hasattr(response, "usage"):
                    await self._cost_tracker.record_usage(
                        response.usage.prompt_tokens, response.usage.completion_tokens
                    )

                return response

            response = await retry_with_exponential_backoff(make_openai_call, max_retries=3)

            comment_text = response.choices[0].message.content.strip()

            # Ensure it starts with @username if not already
            if not comment_text.startswith(f"@{tweet.author}"):
                comment_text = f"@{tweet.author} {comment_text}"

            return comment_text

        except Exception as e:
            logger.error("OpenAI API error: %s", str(e))
            raise

    def _build_generation_prompt(
        self, tweet: Tweet, communication_style: CommunicationStyle
    ) -> str:
        """
        Build the comment generation prompt.
        """
        return f"""
Generate a strategic comment for this tweet following the communication style guidelines:

TWEET TO COMMENT ON:
Author: @{tweet.author}
Text: "{tweet.text}"
Engagement: {tweet.likes} likes, {tweet.reposts} retweets, {tweet.replies} replies

COMMUNICATION STYLE CONTEXT:
Name: {communication_style.name}
Title: {communication_style.title}
Tone: {communication_style.tone_of_voice}

PRINCIPLES TO FOLLOW:
{chr(10).join(f"• {principle}" for principle in communication_style.principles)}

VOCABULARY GUIDELINES:
✅ Encouraged words: {', '.join(communication_style.vocabulary_allowed) if communication_style.vocabulary_allowed else 'None specified'}
❌ Avoid these words: {', '.join(communication_style.vocabulary_prohibited) if communication_style.vocabulary_prohibited else 'None specified'}

FORMATTING RULES:
{chr(10).join(f"• {rule}" for rule in communication_style.formatting_rules) if communication_style.formatting_rules else '• No specific formatting rules'}

CRITICAL REQUIREMENTS:
1. Start with @{tweet.author}
2. ABSOLUTE MAXIMUM: 280 characters total (including @username)
3. Target length: 200-250 characters for safety
4. Write in {communication_style.language.upper()}
5. Be concise, direct, and punchy
6. Every word must add value - no fluff
7. Follow the communication style's tone and principles
8. Make it feel natural, not promotional

IMPORTANT: Count your characters carefully. If your comment exceeds 280 characters, it will be REJECTED and you'll need to try again. Be brief and impactful.

Generate a SHORT, concise comment (max 280 chars including @username):
"""
