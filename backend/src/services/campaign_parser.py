"""
Campaign Parser — parses and formats profiles/keywords for campaigns.

Parsing rules (Properties 7, 8, 10, 11 from design.md):
- Split on commas OR newlines
- Strip surrounding whitespace from each item
- Remove the @ prefix from profile handles
- Remove empty items after stripping
- Keywords are preserved exactly (after trimming)
"""

import re
from typing import List

# Matches one or more commas or newlines (with optional surrounding whitespace)
_DELIMITER_RE = re.compile(r"[,\n]+")


class CampaignParser:
    """Static utility class for parsing and formatting campaign inputs."""

    # ─── Parsing ─────────────────────────────────────────────────────────────

    @staticmethod
    def parse_profiles(raw: str) -> List[str]:
        """
        Parse a comma- or newline-separated string of Twitter handles.

        - Splits on commas and newlines
        - Strips whitespace
        - Removes leading '@' characters
        - Drops empty items

        Example:
            "@elonmusk, @naval\\nsamaltman" → ["elonmusk", "naval", "samaltman"]
        """
        items = _DELIMITER_RE.split(raw)
        result: List[str] = []
        for item in items:
            cleaned = item.strip().lstrip("@")
            if cleaned:
                result.append(cleaned)
        return result

    @staticmethod
    def parse_keywords(raw: str) -> List[str]:
        """
        Parse a comma- or newline-separated string of keywords.

        - Splits on commas and newlines
        - Strips whitespace
        - Preserves exact text (no other modifications)
        - Drops empty items

        Example:
            "AI, machine learning\\nLLM" → ["AI", "machine learning", "LLM"]
        """
        items = _DELIMITER_RE.split(raw)
        return [item.strip() for item in items if item.strip()]

    # ─── Formatting ──────────────────────────────────────────────────────────

    @staticmethod
    def format_profiles(profiles: List[str]) -> str:
        """
        Format a list of profile handles for display, adding '@' prefix.

        Example:
            ["elonmusk", "naval"] → "@elonmusk, @naval"
        """
        return ", ".join(f"@{p}" for p in profiles)

    @staticmethod
    def format_keywords(keywords: List[str]) -> str:
        """
        Format a list of keywords for display.

        Example:
            ["AI", "machine learning"] → "AI, machine learning"
        """
        return ", ".join(keywords)

    @staticmethod
    def format_engagement_filters(
        min_likes: int,
        min_retweets: int,
        min_replies: int,
    ) -> str:
        """
        Format engagement filters as a human-readable string.

        Zero values are shown as 'Sem filtro' (no filter).

        Example:
            (10, 0, 5) → "Mínimo de 10 likes | Sem filtro de retweets | Mínimo de 5 replies"
        """
        parts = []
        parts.append(
            f"Mínimo de {min_likes} likes" if min_likes > 0 else "Sem filtro de likes"
        )
        parts.append(
            f"Mínimo de {min_retweets} retweets" if min_retweets > 0 else "Sem filtro de retweets"
        )
        parts.append(
            f"Mínimo de {min_replies} replies" if min_replies > 0 else "Sem filtro de replies"
        )
        return " | ".join(parts)
