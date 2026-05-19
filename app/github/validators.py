from fastapi import Header, HTTPException


SUPPORTED_EVENTS = ["pull_request"]


def validate_github_event(x_github_event: str = Header(None)):
    if x_github_event not in SUPPORTED_EVENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported GitHub event: {x_github_event}",
        )

    return x_github_event