from pydantic import BaseModel


class ReviewFinding(BaseModel):
    file: str
    severity: str
    line: int
    title: str
    comment: str
    confidence: float


class ReviewResult(BaseModel):
    summary: str
    findings: list[ReviewFinding]
