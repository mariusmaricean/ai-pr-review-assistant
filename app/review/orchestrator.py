from app.ai.client import generate_pr_review
from app.review.context_builder import build_review_context


async def run_review(files: list[dict]) -> str:
    review_context = build_review_context(files)

    review = await generate_pr_review(review_context)

    return review
