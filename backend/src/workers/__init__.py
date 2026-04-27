"""Celery workers and tasks"""

# Import tasks to ensure they are registered with Celery
from .campaign_executor import execute_campaign

__all__ = ["execute_campaign"]
