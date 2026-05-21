from app.config import settings
from app.core.redis_client import redis_client


def build_review_key(repo_name: str, pr_number: int, commit_sha: str | None) -> str:
    return f"review:{repo_name}:{pr_number}:{commit_sha or 'unknown'}"


def build_processing_value(job_id: str | None) -> str:
    return f"processing:{job_id}" if job_id else "processing"


def acquire_review_lock(
    repo_name: str,
    pr_number: int,
    commit_sha: str | None,
    job_id: str | None = None,
) -> bool:
    key = build_review_key(repo_name, pr_number, commit_sha)
    value = build_processing_value(job_id)

    current_value = redis_client.get(key)

    if current_value == value:
        return True

    return bool(
        redis_client.set(
            key,
            value,
            nx=True,
            ex=settings.review_idempotency_ttl_seconds,
        )
    )


def mark_review_completed(repo_name: str, pr_number: int, commit_sha: str | None):
    key = build_review_key(repo_name, pr_number, commit_sha)
    redis_client.set(
        key,
        "completed",
        ex=settings.review_idempotency_ttl_seconds,
    )
