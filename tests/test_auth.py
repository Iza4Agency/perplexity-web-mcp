"""Unit tests for the shared Perplexity authentication protocol."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from perplexity_web_mcp.auth import (
    create_auth_session,
    extract_session_token,
    follow_auth_callback,
    verify_totp,
)
from perplexity_web_mcp.constants import API_BASE_URL, API_VERSION, SESSION_COOKIE_NAME


def response(status: int = 200, *, data: dict | None = None, headers: dict | None = None) -> SimpleNamespace:
    """Build the small response surface used by the auth helpers."""
    return SimpleNamespace(
        status_code=status,
        headers=headers or {},
        text="",
        json=lambda: data or {},
    )


def test_create_auth_session_uses_app_headers_and_returns_csrf() -> None:
    session = MagicMock()
    session.get.side_effect = [response(), response(data={"csrfToken": "csrf-token"})]

    with patch("perplexity_web_mcp.auth.Session", return_value=session) as session_class:
        result_session, csrf = create_auth_session()

    assert result_session is session
    assert csrf == "csrf-token"
    headers = session_class.call_args.kwargs["headers"]
    assert headers["x-app-apiclient"] == "default"
    assert headers["x-app-apiversion"] == API_VERSION


def test_follow_auth_callback_follows_normal_redirect() -> None:
    session = MagicMock()
    session.get.side_effect = [response(302, headers={"Location": "/"}), response()]

    assert follow_auth_callback(session, "https://callback") is None
    session.get.assert_any_call(API_BASE_URL + "/")


def test_follow_auth_callback_returns_totp_challenge() -> None:
    session = MagicMock()
    session.get.return_value = response(302, headers={"Location": "/auth/totp-challenge?token=challenge-123"})

    assert follow_auth_callback(session, "https://callback") == "challenge-123"
    session.get.assert_called_once_with("https://callback", allow_redirects=False)


def test_follow_auth_callback_rejects_error_redirect() -> None:
    session = MagicMock()
    session.get.return_value = response(302, headers={"Location": "/?error=Verification"})

    with pytest.raises(ValueError, match="invalid or expired"):
        follow_auth_callback(session, "https://callback")


def test_verify_totp_follows_json_redirect() -> None:
    session = MagicMock()
    session.post.return_value = response(data={"redirect": "/authenticated"})

    verify_totp(session, "challenge-123", "123456")

    session.post.assert_called_once_with(
        f"{API_BASE_URL}/api/auth/totp-challenge/verify?version={API_VERSION}&source=default",
        json={"token": "challenge-123", "code": "123456"},
        allow_redirects=False,
    )
    session.get.assert_called_once_with(f"{API_BASE_URL}/authenticated")


def test_verify_totp_rejects_invalid_format_without_network_call() -> None:
    session = MagicMock()

    with pytest.raises(ValueError, match="6-digit"):
        verify_totp(session, "challenge-123", "123")

    session.post.assert_not_called()


def test_extract_session_token_reassembles_numeric_cookie_chunks() -> None:
    session = MagicMock()
    session.cookies.get.return_value = None
    session.cookies.items.return_value = [
        (f"{SESSION_COOKIE_NAME}.1", "second"),
        (f"{SESSION_COOKIE_NAME}.0", "first"),
    ]

    assert extract_session_token(session) == "firstsecond"
