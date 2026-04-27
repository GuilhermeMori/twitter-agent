"""
OpenAI API utilities for retry logic, rate limiting, and cost tracking.
"""

import time
import asyncio
from typing import Callable, Any, Optional
from functools import wraps
from openai import OpenAI, RateLimitError, APIError, APIConnectionError
from src.core.logging_config import get_logger

logger = get_logger("utils.openai_utils")

# Cost tracking (per 1M tokens for gpt-4o-mini)
GPT4O_MINI_INPUT_COST = 0.150  # $0.150 per 1M input tokens
GPT4O_MINI_OUTPUT_COST = 0.600  # $0.600 per 1M output tokens


class OpenAIRateLimiter:
    """Rate limiter for OpenAI API calls."""
    
    def __init__(self, max_requests_per_minute: int = 50):
        """
        Initialize rate limiter.
        
        Args:
            max_requests_per_minute: Maximum requests allowed per minute
        """
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until a request slot is available."""
        async with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            # If at limit, wait until oldest request expires
            if len(self.requests) >= self.max_requests:
                sleep_time = 60 - (now - self.requests[0]) + 0.1
                logger.debug("Rate limit reached, waiting %.2f seconds", sleep_time)
                await asyncio.sleep(sleep_time)
                # Retry acquire after waiting
                return await self.acquire()
            
            # Record this request
            self.requests.append(now)


class OpenAICostTracker:
    """Track OpenAI API costs."""
    
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
        self.lock = asyncio.Lock()
    
    async def record_usage(self, input_tokens: int, output_tokens: int):
        """
        Record token usage.
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
        """
        async with self.lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_requests += 1
    
    def get_estimated_cost(self) -> float:
        """
        Calculate estimated cost in USD.
        
        Returns:
            Estimated cost in dollars
        """
        input_cost = (self.total_input_tokens / 1_000_000) * GPT4O_MINI_INPUT_COST
        output_cost = (self.total_output_tokens / 1_000_000) * GPT4O_MINI_OUTPUT_COST
        return input_cost + output_cost
    
    def get_stats(self) -> dict:
        """
        Get usage statistics.
        
        Returns:
            Dictionary with usage stats
        """
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_usd": round(self.get_estimated_cost(), 4)
        }
    
    def reset(self):
        """Reset all counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0


async def retry_with_exponential_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        *args: Arguments to pass to func
        **kwargs: Keyword arguments to pass to func
        
    Returns:
        Result from func
        
    Raises:
        Exception: If all retries fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        except (RateLimitError, APIConnectionError, APIError) as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error("Max retries (%d) reached for OpenAI API call: %s", max_retries, str(e))
                raise
            
            # Calculate delay with exponential backoff
            wait_time = min(delay, max_delay)
            logger.warning(
                "OpenAI API error (attempt %d/%d): %s. Retrying in %.2f seconds...",
                attempt + 1, max_retries + 1, str(e), wait_time
            )
            
            await asyncio.sleep(wait_time)
            delay *= exponential_base
    
    # Should never reach here, but just in case
    raise last_exception


def with_retry_and_rate_limit(
    rate_limiter: Optional[OpenAIRateLimiter] = None,
    cost_tracker: Optional[OpenAICostTracker] = None,
    max_retries: int = 3
):
    """
    Decorator to add retry logic, rate limiting, and cost tracking to OpenAI API calls.
    
    Args:
        rate_limiter: Optional rate limiter instance
        cost_tracker: Optional cost tracker instance
        max_retries: Maximum number of retry attempts
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Apply rate limiting
            if rate_limiter:
                await rate_limiter.acquire()
            
            # Retry with exponential backoff
            result = await retry_with_exponential_backoff(
                func, max_retries=max_retries, *args, **kwargs
            )
            
            # Track costs if tracker provided and result has usage info
            if cost_tracker and hasattr(result, 'usage'):
                await cost_tracker.record_usage(
                    result.usage.prompt_tokens,
                    result.usage.completion_tokens
                )
                logger.debug(
                    "OpenAI usage: %d input tokens, %d output tokens",
                    result.usage.prompt_tokens,
                    result.usage.completion_tokens
                )
            
            return result
        
        return wrapper
    return decorator


# Global instances for shared rate limiting and cost tracking
_global_rate_limiter = OpenAIRateLimiter(max_requests_per_minute=50)
_global_cost_tracker = OpenAICostTracker()


def get_global_rate_limiter() -> OpenAIRateLimiter:
    """Get the global rate limiter instance."""
    return _global_rate_limiter


def get_global_cost_tracker() -> OpenAICostTracker:
    """Get the global cost tracker instance."""
    return _global_cost_tracker


def reset_global_cost_tracker():
    """Reset the global cost tracker."""
    _global_cost_tracker.reset()
    logger.info("Global cost tracker reset")
