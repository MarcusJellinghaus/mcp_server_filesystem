"""Private helpers for extracting diagnostic information from GithubException.

Used by failure-path DEBUG logging across the `github_operations` package to
produce consistent, allow-listed header dumps without leaking secrets or
proxy noise. This module is intentionally private to the package and is not
re-exported via `github_operations/__init__.py`.
"""

from __future__ import annotations

from github.GithubException import GithubException

DIAGNOSTIC_HEADERS: frozenset[str] = frozenset(
    {
        "WWW-Authenticate",
        "X-OAuth-Scopes",
        "X-Accepted-OAuth-Scopes",
        "X-GitHub-Request-Id",
        "X-RateLimit-Remaining",
        "X-RateLimit-Limit",
        "Date",
    }
)


def extract_diagnostic_headers(exc: GithubException) -> dict[str, str]:
    """Return only allow-listed headers from `exc.headers` (case-insensitive lookup).

    Original key casing from `exc.headers` is preserved in the output. Returns
    an empty dict when no headers are present or none match the allow-list.
    """
    headers = exc.headers
    if not headers:
        return {}
    allow_lower = {h.lower() for h in DIAGNOSTIC_HEADERS}
    return {k: v for k, v in headers.items() if k.lower() in allow_lower}
