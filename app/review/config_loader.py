import fnmatch

import yaml

from app.review.config import ReviewConfig


def load_review_config_from_text(config_text: str | None) -> ReviewConfig:
    if not config_text:
        return ReviewConfig()

    data = yaml.safe_load(config_text) or {}

    return ReviewConfig(
        min_confidence=data.get("review", {}).get("min_confidence", 0.7),
        max_comments=data.get("review", {}).get("max_comments", 10),
        ignored_paths=data.get("ignored_paths", []),
    )


def filter_ignored_files(files: list[dict], config: ReviewConfig) -> list[dict]:
    return [
        file
        for file in files
        if not any(
            fnmatch.fnmatch(file.get("filename", ""), pattern)
            for pattern in config.ignored_paths
        )
    ]
