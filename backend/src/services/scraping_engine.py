"""
Twitter Scraping Engine — executes scraping via Apify.

Implements the abstract ScrapingEngine interface and adapts the logic from
the original search-twitter.js agent to Python.

Query construction rules (Properties 12–17 from design.md):
- Profile search: each handle wrapped in "from:<handle>", joined with " OR "
- Keyword search: keywords joined with " OR "
- Language operator "lang:<code>" always appended
- "min_faves:<n>" appended only when min_likes > 0
- "min_replies:<n>" appended only when min_replies > 0
- "since:<date>" appended based on hours_back
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import List

from apify_client import ApifyClient

from src.models.campaign import ScrapingConfig, Tweet
from src.core.logging_config import get_logger

logger = get_logger("services.scraping_engine")

_APIFY_ACTOR = "automation-lab/twitter-scraper"


# ─── Abstract interface ───────────────────────────────────────────────────────


class ScrapingEngine(ABC):
    """Abstract base class for social-network scraping engines."""

    @abstractmethod
    def scrape(self, config: ScrapingConfig) -> List[Tweet]:
        """Execute scraping and return a list of qualifying tweets."""


# ─── Factory ─────────────────────────────────────────────────────────────────


class ScrapingEngineFactory:
    """Creates the appropriate ScrapingEngine for a given social network."""

    @staticmethod
    def create(social_network: str, apify_token: str) -> ScrapingEngine:
        if social_network.lower() == "twitter":
            client = ApifyClient(apify_token)
            return TwitterScrapingEngine(client)
        raise ValueError(f"Unsupported social network: {social_network!r}")


# ─── Twitter implementation ───────────────────────────────────────────────────


class TwitterScrapingEngine(ScrapingEngine):
    """
    Scrapes Twitter via the Apify actor ``automation-lab/twitter-scraper``.

    Applies local post-filtering to guarantee engagement criteria are met,
    since Apify's actor may return tweets that narrowly miss the thresholds.
    """

    def __init__(self, apify_client: ApifyClient) -> None:
        self._client = apify_client

    # ─── Public API ──────────────────────────────────────────────────────────

    def scrape(self, config: ScrapingConfig) -> List[Tweet]:
        """
        Full scraping pipeline:
        1. Build Twitter search query
        2. Invoke Apify actor
        3. Apply local engagement filters
        4. Transform to Tweet models
        """
        query = self.build_query(config)
        logger.info("Scraping Twitter with query: %s", query)

        run_input: dict = {
            "searchTerms": [query],
            "maxResults": 200,
            "mode": "search",
        }

        # Inject Twitter cookies if provided (required for search mode)
        if config.twitter_auth_token and config.twitter_ct0:
            twitter_cookie = f"auth_token={config.twitter_auth_token}; ct0={config.twitter_ct0}"
            run_input["twitterCookie"] = twitter_cookie
        else:
            logger.warning("No Twitter cookies provided - search mode requires authentication")

        # Run the Apify actor synchronously
        run = self._client.actor(_APIFY_ACTOR).call(run_input=run_input)
        dataset_id: str = run["defaultDatasetId"]

        raw_items = list(self._client.dataset(dataset_id).iterate_items())
        logger.info("Apify returned %d raw items", len(raw_items))

        # Apply local filters and transform
        filtered = self.apply_filters(raw_items, config)
        tweets = self.transform_results(filtered)
        logger.info("After filtering: %d qualifying tweets", len(tweets))
        return tweets

    # ─── Query construction ───────────────────────────────────────────────────

    def build_query(self, config: ScrapingConfig) -> str:
        """
        Construct a Twitter search query string from the scraping config.
        """
        parts: List[str] = []

        # Core search term
        if config.search_type.value == "profile" and config.profiles:
            profile_parts = [f"from:{handle}" for handle in config.profiles]
            parts.append(" OR ".join(profile_parts))
        elif config.search_type.value == "keywords" and config.keywords:
            parts.append(" OR ".join(config.keywords))

        # Language filter (always present)
        parts.append(f"lang:{config.language}")

        # Conditional engagement filters
        if config.min_likes > 0:
            parts.append(f"min_faves:{config.min_likes}")
        if config.min_replies > 0:
            parts.append(f"min_replies:{config.min_replies}")

        # Time window - use since AND until for precise date range
        now = datetime.now(tz=timezone.utc)
        since_dt = now - timedelta(days=config.days_back)
        parts.append(f"since:{since_dt.strftime('%Y-%m-%d')}")
        # Add until:today to ensure we only get tweets from the specified range
        parts.append(f"until:{now.strftime('%Y-%m-%d')}")

        return " ".join(parts)

    # ─── Local filtering ──────────────────────────────────────────────────────

    def apply_filters(self, raw_tweets: List[dict], config: ScrapingConfig) -> List[dict]:
        """
        Apply engagement criteria locally to guarantee conformance.
        """
        result = []
        for tweet in raw_tweets:
            likes = tweet.get("likeCount", tweet.get("likes", 0)) or 0
            retweets = tweet.get("retweetCount", tweet.get("retweets", 0)) or 0
            replies = tweet.get("replyCount", tweet.get("replies", 0)) or 0

            if likes < config.min_likes:
                continue
            if retweets < config.min_retweets:
                continue
            if replies < config.min_replies:
                continue
            result.append(tweet)
        return result

    # ─── Transformation ───────────────────────────────────────────────────────

    def transform_results(self, raw_tweets: List[dict]) -> List[Tweet]:
        """
        Transform Apify response dicts into Tweet models.
        """
        tweets: List[Tweet] = []
        for raw in raw_tweets:
            try:
                # Expanded author extraction to cover more Apify actor variations
                author = (
                    raw.get("authorUsername")
                    or raw.get("author", {}).get("userName")
                    or raw.get("author", {}).get("screenName")
                    or raw.get("author", {}).get("user_name")
                    or raw.get("author", {}).get("screen_name")
                    or raw.get("user", {}).get("userName")
                    or raw.get("user", {}).get("screenName")
                    or raw.get("user", {}).get("user_name")
                    or raw.get("user", {}).get("screen_name")
                    or raw.get("username")
                    or raw.get("screenName")
                    or raw.get("screen_name")
                    or raw.get("twitterHandle")
                    or "usuario"  # Fallback
                )

                tweet = Tweet(
                    id=str(raw.get("id", raw.get("tweetId", ""))),
                    url=raw.get("url", raw.get("tweetUrl", "")),
                    author=author,
                    text=raw.get("text", raw.get("fullText", "")),
                    likes=raw.get("likeCount", raw.get("likes", 0)) or 0,
                    reposts=raw.get("retweetCount", raw.get("retweets", 0)) or 0,
                    replies=raw.get("replyCount", raw.get("replies", 0)) or 0,
                    timestamp=_parse_timestamp(raw.get("createdAt", raw.get("timestamp", ""))),
                )
                tweets.append(tweet)
            except Exception as exc:
                logger.warning("Skipping malformed tweet: %s", exc)
        return tweets


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _parse_timestamp(value: str) -> datetime:
    """Parse a Twitter timestamp string into a timezone-aware datetime."""
    if not value:
        return datetime.now(tz=timezone.utc)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        logger.warning("Could not parse timestamp %r, using now()", value)
        return datetime.now(tz=timezone.utc)
