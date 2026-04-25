"""GitHub connectivity and branch protection verification.

Provides verify_github() which runs structured checks against the GitHub API
and returns per-check results. All checks use PyGithub — no gh CLI dependency.
"""

import logging
from pathlib import Path
from typing import Literal, NotRequired, TypedDict

from github import Auth, Github

from mcp_workspace.config import get_github_token
from mcp_workspace.git_operations.remotes import get_repository_identifier
from mcp_workspace.github_operations.base_manager import BaseGitHubManager

logger = logging.getLogger(__name__)


class CheckResult(TypedDict):
    """Result of a single verification check."""

    ok: bool
    value: str
    severity: Literal["error", "warning"]
    error: NotRequired[str]
    install_hint: NotRequired[str]


def verify_github(project_dir: Path) -> dict[str, object]:
    """Verify GitHub connectivity and branch protection.

    Runs checks 1–4 (token, auth, repo URL, repo access) independently.
    Each check reports its own result regardless of earlier failures.

    Args:
        project_dir: Path to the project directory containing a git repository.

    Returns:
        Dict with ``overall_ok`` bool and per-check ``CheckResult`` entries.
    """
    result: dict[str, object] = {}

    # ------------------------------------------------------------------
    # Check 1: token configured
    # ------------------------------------------------------------------
    token = get_github_token()
    if isinstance(token, str):
        # Scopes will be updated after check 2 if auth succeeds
        result["token_configured"] = CheckResult(
            ok=True,
            value="configured (scopes: unknown)",
            severity="error",
        )
    else:
        result["token_configured"] = CheckResult(
            ok=False,
            value="not configured",
            severity="error",
            error="GitHub token not found",
            install_hint=(
                "Set GITHUB_TOKEN environment variable or add [github] token "
                "to ~/.mcp_coder/config.toml"
            ),
        )

    # ------------------------------------------------------------------
    # Check 2: authenticated user (also populates oauth_scopes for check 1)
    # ------------------------------------------------------------------
    try:
        github_client = Github(auth=Auth.Token(token))  # type: ignore[arg-type]
        user = github_client.get_user()
        result["authenticated_user"] = CheckResult(
            ok=True,
            value=user.login,
            severity="error",
        )
        # Update check 1 value with actual scopes
        scopes = github_client.oauth_scopes
        if scopes is not None:
            scope_str = ", ".join(scopes) if scopes else "none"
        else:
            scope_str = "unknown"
        result["token_configured"] = CheckResult(
            ok=True,
            value=f"configured (scopes: {scope_str})",
            severity="error",
        )
    except Exception as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.debug("Authentication check failed: %s", exc)
        result["authenticated_user"] = CheckResult(
            ok=False,
            value="authentication failed",
            severity="error",
            error=str(exc),
        )

    # ------------------------------------------------------------------
    # Check 3: repository URL resolvable
    # ------------------------------------------------------------------
    try:
        identifier = get_repository_identifier(project_dir)
    except Exception as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.debug("Repository identifier lookup failed: %s", exc)
        identifier = None

    if identifier is not None:
        result["repo_url"] = CheckResult(
            ok=True,
            value=identifier.https_url,
            severity="error",
        )
    else:
        result["repo_url"] = CheckResult(
            ok=False,
            value="not resolvable",
            severity="error",
            error="Could not determine repository URL from git remote",
        )

    # ------------------------------------------------------------------
    # Check 4: repository accessible
    # ------------------------------------------------------------------
    try:
        manager = BaseGitHubManager(project_dir=project_dir, github_token=token)
        repo = manager._get_repository()
        if repo is not None:
            result["repo_accessible"] = CheckResult(
                ok=True,
                value=repo.full_name,
                severity="error",
            )
        else:
            result["repo_accessible"] = CheckResult(
                ok=False,
                value="not accessible",
                severity="error",
                error="Repository returned None from GitHub API",
            )
    except (ValueError, Exception) as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.debug("Repository access check failed: %s", exc)
        result["repo_accessible"] = CheckResult(
            ok=False,
            value="not accessible",
            severity="error",
            error=str(exc),
        )

    # ------------------------------------------------------------------
    # overall_ok: all error-severity checks must pass
    # ------------------------------------------------------------------
    check_keys = ("token_configured", "authenticated_user", "repo_url", "repo_accessible")
    error_checks: list[CheckResult] = []
    for k in check_keys:
        check = result[k]
        if isinstance(check, dict) and check.get("severity") == "error":
            error_checks.append(check)  # type: ignore[arg-type]
    result["overall_ok"] = all(c["ok"] for c in error_checks)

    return result
