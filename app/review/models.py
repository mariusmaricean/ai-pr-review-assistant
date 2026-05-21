from pydantic import BaseModel
from typing import List


class ReviewFinding(BaseModel):
    file: str
    severity: str
    line: int
    title: str
    comment: str
    confidence: float


class ReviewResult(BaseModel):
    summary: str
    findings: List[ReviewFinding]
