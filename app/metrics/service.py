from app.core.redis_client import redis_client


def record_review_metrics(
    repository: str,
    language: str | None,
    duration_seconds: float,
    findings_count: int,
    published_as: str,
):
    redis_client.incr("metrics:reviews:total")
    redis_client.incrby("metrics:findings:total", findings_count)
    redis_client.incrbyfloat("metrics:reviews:duration_total", duration_seconds)

    redis_client.hincrby("metrics:repositories", repository, 1)
    redis_client.hincrby("metrics:publish_modes", published_as, 1)

    if language:
        redis_client.hincrby("metrics:languages", language, 1)


def get_review_metrics():
    total_reviews = int(redis_client.get("metrics:reviews:total") or 0)
    total_findings = int(redis_client.get("metrics:findings:total") or 0)
    total_duration = float(redis_client.get("metrics:reviews:duration_total") or 0)

    avg_duration = total_duration / total_reviews if total_reviews else 0
    avg_findings = total_findings / total_reviews if total_reviews else 0

    return {
        "total_reviews": total_reviews,
        "total_findings": total_findings,
        "avg_review_duration_seconds": round(avg_duration, 2),
        "avg_findings_per_review": round(avg_findings, 2),
        "repositories": redis_client.hgetall("metrics:repositories"),
        "languages": redis_client.hgetall("metrics:languages"),
        "publish_modes": redis_client.hgetall("metrics:publish_modes"),
    }
