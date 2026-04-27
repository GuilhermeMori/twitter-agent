"""
Campaign Validator — validates campaign creation requests.

Implements the validation rules from design.md Properties 4–9 and
Requirements 3.1–3.6.
"""

from src.models.campaign import CampaignCreateDTO, SearchType, ValidationResult
from src.services.campaign_parser import CampaignParser


class CampaignValidator:
    """Validates campaign creation data against business rules."""

    def validate_create(self, data: CampaignCreateDTO) -> ValidationResult:
        """
        Full validation of a campaign creation request.

        Checks:
        1. Campaign name is not empty (Property 4)
        2. Search type is valid
        3. Profiles or keywords are present based on search type (Properties 5, 6)
        4. Engagement filters are non-negative (Property 9)
        """
        errors: dict[str, str] = {}

        # 1. Name must not be blank
        if not data.name or not data.name.strip():
            errors["name"] = "Campaign name cannot be empty"

        # 2. Validate search-type-specific fields
        search_result = self.validate_search_config(data)
        if not search_result.is_valid:
            errors.update(search_result.errors)

        # 3. Engagement filters must be non-negative
        filter_result = self.validate_engagement_filters(
            data.min_likes, data.min_retweets, data.min_replies
        )
        if not filter_result.is_valid:
            errors.update(filter_result.errors)

        if errors:
            return ValidationResult.fail_many(errors)
        return ValidationResult.ok()

    def validate_search_config(self, data: CampaignCreateDTO) -> ValidationResult:
        """
        Validate that the correct search fields are present for the chosen
        search type.

        - Profile search requires at least one non-empty profile (Property 5)
        - Keyword search requires at least one non-empty keyword (Property 6)
        """
        if data.search_type == SearchType.PROFILE:
            if not data.profiles or not data.profiles.strip():
                return ValidationResult.fail(
                    "profiles", "At least one profile is required for profile search"
                )
            parsed = CampaignParser.parse_profiles(data.profiles)
            if not parsed:
                return ValidationResult.fail(
                    "profiles",
                    "No valid profiles found after parsing — check for empty entries",
                )

        elif data.search_type == SearchType.KEYWORDS:
            if not data.keywords or not data.keywords.strip():
                return ValidationResult.fail(
                    "keywords", "At least one keyword is required for keyword search"
                )
            parsed_kw = CampaignParser.parse_keywords(data.keywords)
            if not parsed_kw:
                return ValidationResult.fail(
                    "keywords",
                    "No valid keywords found after parsing — check for empty entries",
                )

        return ValidationResult.ok()

    @staticmethod
    def validate_engagement_filters(
        min_likes: int,
        min_retweets: int,
        min_replies: int,
    ) -> ValidationResult:
        """
        Validate that all engagement filter values are non-negative (Property 9).
        """
        errors: dict[str, str] = {}
        if min_likes < 0:
            errors["min_likes"] = "min_likes must be non-negative"
        if min_retweets < 0:
            errors["min_retweets"] = "min_retweets must be non-negative"
        if min_replies < 0:
            errors["min_replies"] = "min_replies must be non-negative"

        if errors:
            return ValidationResult.fail_many(errors)
        return ValidationResult.ok()
