from app.config import settings
from app.review.guards import validate_review_size


def test_validate_review_size_allows_small_pr():
    old_max_files = settings.max_changed_files
    old_max_patch = settings.max_patch_chars
    settings.max_changed_files = 2
    settings.max_patch_chars = 20

    try:
        is_valid, error = validate_review_size([
            {"filename": "app/main.py", "patch": "+hello"},
        ])
    finally:
        settings.max_changed_files = old_max_files
        settings.max_patch_chars = old_max_patch

    assert is_valid is True
    assert error is None


def test_validate_review_size_blocks_too_many_files():
    old_max_files = settings.max_changed_files
    settings.max_changed_files = 1

    try:
        is_valid, error = validate_review_size([
            {"filename": "a.py", "patch": "+a"},
            {"filename": "b.py", "patch": "+b"},
        ])
    finally:
        settings.max_changed_files = old_max_files

    assert is_valid is False
    assert error == "PR has too many changed files: 2"


def test_validate_review_size_blocks_large_patch():
    old_max_patch = settings.max_patch_chars
    settings.max_patch_chars = 5

    try:
        is_valid, error = validate_review_size([
            {"filename": "a.py", "patch": "123456"},
        ])
    finally:
        settings.max_patch_chars = old_max_patch

    assert is_valid is False
    assert error == "PR diff is too large: 6 chars"
