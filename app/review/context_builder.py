def build_review_context(files: list[dict]) -> str:
    sections = []

    for file in files:
        filename = file.get("filename")
        status = file.get("status")
        patch = file.get("patch", "")

        if not patch:
            continue

        sections.append(
            f"""
File: {filename}
Status: {status}

Diff:
{patch}
"""
        )

    return "\n---\n".join(sections)
