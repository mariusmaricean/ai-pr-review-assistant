import re

from app.review.models import ReviewFinding


HUNK_HEADER_PATTERN = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def map_findings_to_inline_comments(
    files: list[dict],
    findings: list[ReviewFinding],
) -> list[dict]:
    line_positions = _build_line_positions(files)
    comments = []

    for finding in findings:
        if not finding.line:
            continue

        position = line_positions.get((finding.filename, finding.line))
        if position is None:
            continue

        comments.append(
            {
                "path": finding.filename,
                "position": position,
                "body": _format_inline_comment_body(finding),
            }
        )

    return comments


def _build_line_positions(files: list[dict]) -> dict[tuple[str, int], int]:
    line_positions = {}

    for file in files:
        filename = file.get("filename")
        patch = file.get("patch")

        if not filename or not patch:
            continue

        current_new_line: int | None = None
        position = 0

        for patch_line in patch.splitlines():
            hunk_match = HUNK_HEADER_PATTERN.match(patch_line)

            if hunk_match:
                current_new_line = int(hunk_match.group(1))
                continue

            if current_new_line is None:
                continue

            position += 1

            if patch_line.startswith("+") or patch_line.startswith(" "):
                line_positions[(filename, current_new_line)] = position
                current_new_line += 1

    return line_positions


def _format_inline_comment_body(finding: ReviewFinding) -> str:
    severity = finding.severity.title()
    confidence = round(finding.confidence, 2)

    return f"**{severity} severity** | Confidence: {confidence}\n\n{finding.body}"
