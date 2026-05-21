import re


def extract_changed_lines(patch: str) -> list[int]:
    changed_lines = []

    current_line = 0

    for line in patch.splitlines():
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)

            if match:
                current_line = int(match.group(1))

        elif line.startswith("+") and not line.startswith("+++"):
            changed_lines.append(current_line)
            current_line += 1

        elif line.startswith("-"):
            continue

        else:
            current_line += 1

    return changed_lines
