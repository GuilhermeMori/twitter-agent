"""Celery application configuration"""

from celery import Celery
from celery.utils.log import get_task_logger
from src.core.config import settings

logger = get_task_logger(__name__)

celery_app = Celery(
    "twitter_scraping_saas",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    # Serialisation
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task tracking
    task_track_started=True,
    task_acks_late=True,           # Acknowledge only after task completes
    worker_prefetch_multiplier=1,  # One task at a time per worker (fair dispatch)

    # Time limits
    task_time_limit=3600,          # Hard limit: 1 hour
    task_soft_time_limit=3300,     # Soft limit: 55 minutes (raises SoftTimeLimitExceeded)

    # Retry defaults (overridden per-task where needed)
    task_max_retries=3,
    task_default_retry_delay=60,   # 1 minute base delay

    # Result expiry
    result_expires=86400,          # Keep results for 24 hours

    # Worker concurrency (can be overridden via CLI --concurrency flag)
    worker_concurrency=4,

    # Beat schedule (placeholder for future scheduled tasks)
    beat_schedule={},
)

# Auto-discover tasks in the workers and tasks packages
celery_app.autodiscover_tasks(["src.workers", "src.tasks"])
