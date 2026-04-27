"""Base Celery task with shared retry and error-handling behaviour"""

import time
from celery import Task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# Exponential backoff delays (seconds) for retries 1, 2, 3
RETRY_DELAYS = [1, 2, 4]


class BaseTask(Task):
    """
    Base task class that provides:
    - Exponential backoff retry delays
    - Structured logging on failure / retry
    - Max 3 retries by default
    """

    abstract = True
    max_retries = 3
    acks_late = True

    def on_failure(self, exc: Exception, task_id: str, args, kwargs, einfo) -> None:
        """Called when the task raises an unhandled exception after all retries."""
        logger.error(
            "Task %s[%s] failed permanently: %s",
            self.name,
            task_id,
            exc,
            exc_info=einfo,
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc: Exception, task_id: str, args, kwargs, einfo) -> None:
        """Called when the task is about to be retried."""
        retry_num = self.request.retries
        delay = RETRY_DELAYS[min(retry_num, len(RETRY_DELAYS) - 1)]
        logger.warning(
            "Task %s[%s] retry %d/%d in %ds: %s",
            self.name,
            task_id,
            retry_num + 1,
            self.max_retries,
            delay,
            exc,
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def retry_with_backoff(self, exc: Exception) -> None:
        """
        Convenience method to retry with exponential backoff.

        Call inside a task:
            except SomeTransientError as e:
                self.retry_with_backoff(e)
        """
        retry_num = self.request.retries
        delay = RETRY_DELAYS[min(retry_num, len(RETRY_DELAYS) - 1)]
        raise self.retry(exc=exc, countdown=delay)
