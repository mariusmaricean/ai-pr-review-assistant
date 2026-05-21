from app.ai.client import generate_pr_review
from app.review.context_builder import build_review_context
from app.review.models import ReviewResult


async def run_review(files: list[dict]) -> ReviewResult:
    review_context = build_review_context(files)

    return await generate_pr_review(review_context)
