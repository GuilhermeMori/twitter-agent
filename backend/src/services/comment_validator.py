"""Comment validation service for validating generated comments against persona rules"""

import re
from typing import List
from src.models.tweet_comment import CommentValidationResult
from src.models.communication_style import CommunicationStyle
from src.core.logging_config import get_logger

logger = get_logger("services.comment_validator")


class CommentValidator:
    """Validates generated comments against persona rules and general requirements."""

    # Emoji pattern to detect emojis in text
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )

    # URL pattern to detect links
    URL_PATTERN = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        re.IGNORECASE
    )

    def validate(
        self, 
        comment: str, 
        communication_style: CommunicationStyle,
        tweet_author: str
    ) -> CommentValidationResult:
        """
        Validate a comment against persona rules and general requirements.
        
        Args:
            comment: The generated comment text
            communication_style: The communication style used to generate the comment
            tweet_author: The Twitter username of the tweet author
            
        Returns:
            CommentValidationResult with validation status and errors
        """
        errors = []
        char_count = len(comment)
        
        try:
            # 1. Check length (max 280 characters)
            if char_count > 280:
                errors.append(f"Comment exceeds 280 characters ({char_count})")
            
            # 2. Check minimum length (at least 10 characters)
            if char_count < 10:
                errors.append(f"Comment too short ({char_count} characters, minimum 10)")
            
            # 3. Check @username mention (case-insensitive)
            username_mention = f"@{tweet_author}".lower()
            if username_mention not in comment.lower():
                errors.append(f"Comment must mention {username_mention}")
            
            # 4. Check forbidden vocabulary
            if communication_style.vocabulary_prohibited:
                for word in communication_style.vocabulary_prohibited:
                    if word.lower() in comment.lower():
                        errors.append(f"Comment contains forbidden word: '{word}'")
            
            # 5. Check formatting rules
            if communication_style.formatting_rules:
                for rule in communication_style.formatting_rules:
                    rule_lower = rule.lower()
                    
                    # No emojis rule
                    if "no emoji" in rule_lower or "🚫" in rule:
                        if self._contains_emoji(comment):
                            errors.append("Comment contains emojis (forbidden by communication style)")
                    
                    # No links rule
                    if "no link" in rule_lower:
                        if self._contains_url(comment):
                            errors.append("Comment contains links (forbidden by communication style)")
                    
                    # Maximum character limit from formatting rules
                    char_limit_match = re.search(r'maximum (\d+) character', rule_lower)
                    if char_limit_match:
                        max_chars = int(char_limit_match.group(1))
                        if char_count > max_chars:
                            errors.append(f"Comment exceeds communication style limit of {max_chars} characters")
            
            # 6. Check language (basic check for English if specified)
            if communication_style.language == "en":
                if not self._is_likely_english(comment):
                    errors.append("Comment does not appear to be in English")
            
            # 7. Check for excessive capitalization
            if self._has_excessive_caps(comment):
                errors.append("Comment has excessive capitalization (appears to be shouting)")
            
            # 8. Check for spam-like patterns
            if self._appears_spammy(comment):
                errors.append("Comment appears to have spam-like characteristics")
            
            # Return validation result
            if errors:
                logger.warning("Comment validation failed: %s", errors)
                return CommentValidationResult.invalid(errors, char_count)
            else:
                logger.info("Comment validation passed (%d characters)", char_count)
                return CommentValidationResult.valid(char_count)
                
        except Exception as e:
            logger.error("Error during comment validation: %s", str(e))
            errors.append(f"Validation error: {str(e)}")
            return CommentValidationResult.invalid(errors, char_count)

    def _contains_emoji(self, text: str) -> bool:
        """Check if text contains emoji characters."""
        return bool(self.EMOJI_PATTERN.search(text))

    def _contains_url(self, text: str) -> bool:
        """Check if text contains URLs."""
        return bool(self.URL_PATTERN.search(text))

    def _is_likely_english(self, text: str) -> bool:
        """
        Basic check if text is likely in English.
        This is a simple heuristic, not a comprehensive language detector.
        """
        # Remove @mentions and common punctuation
        clean_text = re.sub(r'@\w+', '', text)
        clean_text = re.sub(r'[^\w\s]', '', clean_text)
        
        # Check if text contains mostly ASCII characters
        ascii_chars = sum(1 for c in clean_text if ord(c) < 128)
        total_chars = len(clean_text.replace(' ', ''))
        
        if total_chars == 0:
            return True  # Empty text is considered valid
        
        ascii_ratio = ascii_chars / total_chars
        return ascii_ratio > 0.8  # At least 80% ASCII characters

    def _has_excessive_caps(self, text: str) -> bool:
        """Check if text has excessive capitalization."""
        # Remove @mentions and URLs for this check
        clean_text = re.sub(r'@\w+', '', text)
        clean_text = re.sub(self.URL_PATTERN, '', clean_text)
        
        # Count letters
        letters = [c for c in clean_text if c.isalpha()]
        if len(letters) < 10:  # Too short to judge
            return False
        
        caps = sum(1 for c in letters if c.isupper())
        caps_ratio = caps / len(letters)
        
        # More than 50% caps is considered excessive
        return caps_ratio > 0.5

    def _appears_spammy(self, text: str) -> bool:
        """Check for spam-like characteristics."""
        # Check for excessive repetition of characters
        if re.search(r'(.)\1{4,}', text):  # Same character repeated 5+ times
            return True
        
        # Check for excessive exclamation marks
        if text.count('!') > 3:
            return True
        
        # Check for excessive question marks
        if text.count('?') > 2:
            return True
        
        # Check for common spam phrases
        spam_phrases = [
            'click here', 'buy now', 'limited time', 'act now',
            'free money', 'make money fast', 'guaranteed',
            'no risk', '100% free', 'call now'
        ]
        
        text_lower = text.lower()
        for phrase in spam_phrases:
            if phrase in text_lower:
                return True
        
        return False

    def get_validation_summary(self, results: List[CommentValidationResult]) -> dict:
        """
        Get a summary of validation results for multiple comments.
        
        Args:
            results: List of validation results
            
        Returns:
            Dictionary with validation statistics
        """
        if not results:
            return {
                "total_comments": 0,
                "valid_comments": 0,
                "invalid_comments": 0,
                "validation_rate": 0.0,
                "common_errors": []
            }
        
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = len(results) - valid_count
        validation_rate = valid_count / len(results) * 100
        
        # Collect all errors
        all_errors = []
        for result in results:
            if not result.is_valid:
                all_errors.extend(result.errors)
        
        # Count error frequency
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        # Get most common errors
        common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_comments": len(results),
            "valid_comments": valid_count,
            "invalid_comments": invalid_count,
            "validation_rate": round(validation_rate, 1),
            "common_errors": [{"error": error, "count": count} for error, count in common_errors]
        }