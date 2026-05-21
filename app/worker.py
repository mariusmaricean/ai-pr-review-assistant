from celery import Celery

from app.config import settings


celery_app = Celery(
    "ai_pr_review_assistant",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)
