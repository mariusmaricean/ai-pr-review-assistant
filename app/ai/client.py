from openai import AsyncOpenAI

from app.ai.prompts import REVIEW_SYSTEM_PROMPT
from app.config import settings


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
