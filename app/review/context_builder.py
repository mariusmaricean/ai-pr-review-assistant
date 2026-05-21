from app.review.diff_parser import extract_changed_lines


def build_review_context(files: list[dict]) -> str:
    sections = []

    for file in files:
        filename = file.get("filename")
        status = file.get("status")
        patch = file.get("patch", "")

        if not patch:
            continue

        valid_lines = extract_changed_lines(patch)

        sections.append(
            f"""
File: {filename}
Status: {status}

Valid comment lines:
{valid_lines}

Diff:
{patch}
"""
        )

    return "\n---\n".join(sections)
