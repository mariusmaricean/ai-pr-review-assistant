import json

from openai import AsyncOpenAI

from app.ai.prompts import REVIEW_SYSTEM_PROMPT, build_language_prompt
from app.config import settings
from app.review.models import ReviewResult


client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_pr_review(review_context: str, language: str) -> ReviewResult:
    language_instructions = build_language_prompt(language)

    prompt = f"""
Review this pull request diff.

Language/profile:
{language}

Additional review focus:
{language_instructions}

PR diff:
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

    content = response.choices[0].message.content

    parsed = json.loads(content)

    return ReviewResult(**parsed)
