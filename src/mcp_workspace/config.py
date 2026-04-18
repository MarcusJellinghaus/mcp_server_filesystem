"""Configuration helpers for GitHub token and test repo resolution."""

import os
import tomllib
from pathlib import Path


def _read_config_value(section: str, key: str) -> str | None:
    """Read a value from ~/.mcp_coder/config.toml."""
    config_path = Path.home() / ".mcp_coder" / "config.toml"
    if not config_path.exists():
        return None
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        return data.get(section, {}).get(key)  # type: ignore[no-any-return]
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        return None


def get_github_token() -> str | None:
    """Resolve GitHub token: env var → config file → None."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    token = _read_config_value("github", "token")
    if token:
        return token
    return None


def get_test_repo_url() -> str | None:
    """Resolve test repo URL: env var → config file → None."""
    url = os.environ.get("GITHUB_TEST_REPO_URL")
    if url:
        return url
    url = _read_config_value("github", "test_repo_url")
    if url:
        return url
    return None
