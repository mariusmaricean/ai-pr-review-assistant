from pydantic import BaseModel


class ReviewConfig(BaseModel):
    min_confidence: float = 0.7
    max_comments: int = 10
    ignored_paths: list[str] = []
