from app.review.diff_parser import extract_changed_lines


def build_valid_line_map(files: list[dict]) -> dict[str, set[int]]:
    valid_line_map = {}

    for file in files:
        filename = file.get("filename")
        patch = file.get("patch", "")

        if not filename or not patch:
            continue

        valid_line_map[filename] = set(extract_changed_lines(patch))

    return valid_line_map


def filter_findings_to_valid_lines(findings, files: list[dict]):
    valid_line_map = build_valid_line_map(files)

    return [
        finding
        for finding in findings
        if finding.file in valid_line_map
        and finding.line in valid_line_map[finding.file]
    ]
