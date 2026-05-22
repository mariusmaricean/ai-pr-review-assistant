import pytest
from fastapi import HTTPException

from app.config import settings
from app.core.auth import verify_admin_token


def test_verify_admin_token_accepts_matching_token_with_whitespace_and_quotes():
    old_token = settings.admin_api_token
    settings.admin_api_token = "secret-token"

    try:
        assert verify_admin_token('  "secret-token"  ') is None
    finally:
        settings.admin_api_token = old_token


def test_verify_admin_token_rejects_invalid_token():
    old_token = settings.admin_api_token
    settings.admin_api_token = "secret-token"

    try:
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token("wrong-token")
    finally:
        settings.admin_api_token = old_token

    assert exc_info.value.status_code == 401


def test_verify_admin_token_fails_closed_when_unconfigured():
    old_token = settings.admin_api_token
    settings.admin_api_token = ""

    try:
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token("anything")
    finally:
        settings.admin_api_token = old_token

    assert exc_info.value.status_code == 500
