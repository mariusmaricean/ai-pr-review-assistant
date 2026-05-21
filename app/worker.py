from celery import Celery

from app.config import settings
from app.core.logging import configure_logging


configure_logging()

celery_app = Celery(
    "ai_pr_review_assistant",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)
