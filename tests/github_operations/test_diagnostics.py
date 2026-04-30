"""Unit tests for `_diagnostics` helper module."""

from __future__ import annotations

from typing import Any

from github.GithubException import GithubException

from mcp_workspace.github_operations._diagnostics import (
    DIAGNOSTIC_HEADERS,
    extract_diagnostic_headers,
)


def _make_exception(headers: Any) -> GithubException:
    """Build a GithubException with the given headers attribute."""
    exc = GithubException(401, {"message": "Bad credentials"}, headers)
    return exc


class TestDiagnosticHeadersConstant:
    """Tests for the DIAGNOSTIC_HEADERS allow-list."""

    def test_diagnostic_headers_is_frozenset(self) -> None:
        assert isinstance(DIAGNOSTIC_HEADERS, frozenset)

    def test_diagnostic_headers_contains_expected_seven(self) -> None:
        expected = {
            "WWW-Authenticate",
            "X-OAuth-Scopes",
            "X-Accepted-OAuth-Scopes",
            "X-GitHub-Request-Id",
            "X-RateLimit-Remaining",
            "X-RateLimit-Limit",
            "Date",
        }
        assert set(DIAGNOSTIC_HEADERS) == expected


class TestExtractDiagnosticHeaders:
    """Tests for extract_diagnostic_headers()."""

    def test_none_headers_returns_empty_dict(self) -> None:
        exc = _make_exception(None)
        assert extract_diagnostic_headers(exc) == {}

    def test_empty_headers_returns_empty_dict(self) -> None:
        exc = _make_exception({})
        assert extract_diagnostic_headers(exc) == {}

    def test_all_listed_headers_returned_verbatim(self) -> None:
        headers = {
            "WWW-Authenticate": "Bearer",
            "X-OAuth-Scopes": "repo",
            "X-Accepted-OAuth-Scopes": "repo",
            "X-GitHub-Request-Id": "ABCD:1234",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Limit": "60",
            "Date": "Wed, 30 Apr 2026 12:00:00 GMT",
        }
        exc = _make_exception(headers)
        result = extract_diagnostic_headers(exc)
        assert result == headers

    def test_mixed_listed_and_unlisted_only_listed_returned(self) -> None:
        headers = {
            "X-GitHub-Request-Id": "ABCD:1234",
            "Set-Cookie": "session=abc",
            "X-Proxy-Foo": "bar",
            "WWW-Authenticate": "Bearer",
        }
        exc = _make_exception(headers)
        result = extract_diagnostic_headers(exc)
        assert result == {
            "X-GitHub-Request-Id": "ABCD:1234",
            "WWW-Authenticate": "Bearer",
        }

    def test_lowercase_keys_match_and_are_returned(self) -> None:
        headers = {
            "x-github-request-id": "ABCD:1234",
            "www-authenticate": "Bearer",
        }
        exc = _make_exception(headers)
        result = extract_diagnostic_headers(exc)
        assert result == {
            "x-github-request-id": "ABCD:1234",
            "www-authenticate": "Bearer",
        }

    def test_mixed_case_keys_match_and_are_returned(self) -> None:
        headers = {
            "X-GitHub-Request-Id": "ABCD:1234",
            "X-RateLimit-Remaining": "5",
        }
        exc = _make_exception(headers)
        result = extract_diagnostic_headers(exc)
        assert result == headers

    def test_unlisted_headers_excluded(self) -> None:
        headers = {
            "Set-Cookie": "session=abc",
            "X-Proxy-Foo": "bar",
            "Content-Type": "application/json",
        }
        exc = _make_exception(headers)
        result = extract_diagnostic_headers(exc)
        assert result == {}
