"""Supabase database client configuration"""

from functools import lru_cache
from supabase import create_client, Client
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger("core.database")


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Get a cached Supabase client instance.

    Uses lru_cache to ensure a single client is reused across the application,
    providing connection pooling behaviour.
    """
    logger.info("Initialising Supabase client")
    client = create_client(settings.supabase_url, settings.supabase_key)
    logger.info("Supabase client initialised successfully")
    return client


def get_db() -> Client:
    """
    Dependency-injection helper for FastAPI routes.

    Usage:
        @router.get("/example")
        async def example(db: Client = Depends(get_db)):
            ...
    """
    return get_supabase_client()
