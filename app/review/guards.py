from app.config import settings


def validate_review_size(files: list[dict]) -> tuple[bool, str | None]:
    if len(files) > settings.max_changed_files:
        return False, f"PR has too many changed files: {len(files)}"

    total_patch_chars = sum(
        len(file.get("patch", ""))
        for file in files
    )

    if total_patch_chars > settings.max_patch_chars:
        return False, f"PR diff is too large: {total_patch_chars} chars"

    return True, None
