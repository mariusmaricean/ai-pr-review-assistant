from typing import Literal

from pydantic import BaseModel, Field, field_validator


Severity = Literal["high", "medium", "low"]


class ReviewFinding(BaseModel):
    severity: Severity = "low"
    filename: str
    line: int | None = None
    body: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower()

        return value


class StructuredReview(BaseModel):
    summary: str = ""
    findings: list[ReviewFinding] = Field(default_factory=list)
    suggested_improvements: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        sections = [
            "## Summary",
            self.summary or "No summary provided.",
            "",
            "## Findings",
            "",
        ]

        for severity in ("high", "medium", "low"):
            title = severity.title()
            matching_findings = [
                finding for finding in self.findings if finding.severity == severity
            ]

            sections.append(f"### {title} Severity")

            if matching_findings:
                for finding in matching_findings:
                    location = finding.filename
                    if finding.line:
                        location = f"{location}:{finding.line}"
                    sections.append(f"- {location} - {finding.body}")
            else:
                sections.append("- None")

            sections.append("")

        sections.extend(["## Suggested Improvements"])

        if self.suggested_improvements:
            sections.extend(
                f"- {improvement}" for improvement in self.suggested_improvements
            )
        else:
            sections.append("- None")

        return "\n".join(sections)
