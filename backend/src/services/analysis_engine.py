"""
Analysis Engine — analyses collected tweets using the OpenAI API.

Sends a structured prompt containing tweet data and parses the JSON response
into an Analysis model. Handles rate-limit and API errors gracefully.
"""

from __future__ import annotations

import json
import re
from typing import List

from openai import OpenAI, RateLimitError, APIError

from src.models.campaign import Tweet
from src.models.analysis import Analysis
from src.core.logging_config import get_logger

logger = get_logger("services.analysis_engine")

_MODEL = "gpt-4o-mini"
_MAX_TWEETS_IN_PROMPT = 50   # cap to stay within token limits
_MAX_TWEET_CHARS = 280       # truncate very long tweets


class AnalysisEngine:
    """Analyses tweet collections using the OpenAI Chat Completions API."""

    def __init__(self, openai_client: OpenAI) -> None:
        self._client = openai_client

    # ─── Public API ──────────────────────────────────────────────────────────

    def analyze(self, tweets: List[Tweet]) -> Analysis:
        """
        Analyse a list of tweets and return a structured Analysis.

        Raises RuntimeError on unrecoverable API failures.
        """
        if not tweets:
            logger.warning("No tweets to analyse — returning empty analysis")
            return Analysis(
                summary="No tweets were collected for this campaign.",
                key_themes=[],
                sentiment="neutral",
                top_influencers=[],
                recommendations=[],
            )

        prompt = self.prepare_prompt(tweets)
        logger.info("Sending %d tweets to OpenAI for analysis", min(len(tweets), _MAX_TWEETS_IN_PROMPT))

        try:
            response = self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a social media analyst. Analyse the provided tweets "
                            "and return a JSON object with the following keys: "
                            "summary (string), key_themes (array of strings), "
                            "sentiment (string: positive/negative/neutral/mixed), "
                            "top_influencers (array of @handle strings), "
                            "recommendations (array of strings). "
                            "Return ONLY valid JSON, no markdown fences."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )
        except RateLimitError as exc:
            logger.error("OpenAI rate limit exceeded: %s", exc)
            raise RuntimeError("OpenAI rate limit exceeded — please retry later") from exc
        except APIError as exc:
            logger.error("OpenAI API error: %s", exc)
            raise RuntimeError(f"OpenAI API error: {exc}") from exc

        raw_text = response.choices[0].message.content or ""
        return self.parse_response(raw_text)

    # ─── Prompt construction ─────────────────────────────────────────────────

    def prepare_prompt(self, tweets: List[Tweet]) -> str:
        """
        Build the user-facing prompt containing tweet data.

        Caps at _MAX_TWEETS_IN_PROMPT to avoid exceeding token limits.
        """
        sample = tweets[:_MAX_TWEETS_IN_PROMPT]
        lines: List[str] = [f"Analyse the following {len(sample)} tweets:\n"]
        for i, tweet in enumerate(sample, 1):
            text = tweet.text[:_MAX_TWEET_CHARS]
            lines.append(
                f"{i}. @{tweet.author} | ❤️{tweet.likes} 🔁{tweet.reposts} 💬{tweet.replies}\n"
                f"   {text}"
            )
        return "\n".join(lines)

    # ─── Response parsing ────────────────────────────────────────────────────

    def parse_response(self, raw: str) -> Analysis:
        """
        Parse the OpenAI JSON response into an Analysis model.

        Falls back to a minimal Analysis if the response cannot be parsed.
        """
        # Strip any accidental markdown fences
        cleaned = re.sub(r"```(?:json)?", "", raw).strip()
        try:
            data = json.loads(cleaned)
            return Analysis(
                summary=str(data.get("summary", "")),
                key_themes=list(data.get("key_themes", [])),
                sentiment=str(data.get("sentiment", "neutral")),
                top_influencers=list(data.get("top_influencers", [])),
                recommendations=list(data.get("recommendations", [])),
            )
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Could not parse OpenAI response as JSON: %s", exc)
            return Analysis(
                summary=raw[:500] if raw else "Analysis unavailable.",
                key_themes=[],
                sentiment="neutral",
                top_influencers=[],
                recommendations=[],
            )
