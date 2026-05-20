import json

from openai import AsyncOpenAI

from app.ai.prompts import REVIEW_SYSTEM_PROMPT, STRUCTURED_REVIEW_SYSTEM_PROMPT
from app.config import settings
from app.review.models import StructuredReview


client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_pr_review(review_context: str) -> str:
    prompt = f"""
Review this pull request diff:

{review_context}
"""

    response = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": REVIEW_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
    )

    return response.choices[0].message.content


async def generate_structured_pr_review(review_context: str) -> StructuredReview:
    prompt = f"""
Review this pull request diff:

{review_context}
"""

    response = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": STRUCTURED_REVIEW_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    data = json.loads(content)

    return StructuredReview.model_validate(data)
