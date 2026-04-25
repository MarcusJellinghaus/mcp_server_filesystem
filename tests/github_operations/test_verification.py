"""Unit tests for verify_github() connectivity and branch protection checks."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from github.GithubException import GithubException

from mcp_workspace.github_operations.verification import CheckResult, verify_github

MODULE = "mcp_workspace.github_operations.verification"


@pytest.fixture
def _mock_git_repo(tmp_path: Path) -> Path:
    """Return tmp_path after patching is_git_repository to accept it."""
    return tmp_path


def _make_mock_protection(
    *,
    strict: bool = True,
    contexts: list[str] | None = None,
    allow_force_pushes: bool = False,
    allow_deletions: bool = False,
    has_status_checks: bool = True,
) -> Mock:
    """Create a mock BranchProtection object."""
    protection = Mock()
    if has_status_checks:
        status_checks = Mock()
        status_checks.strict = strict
        status_checks.contexts = (
            contexts if contexts is not None else ["ci/test", "ci/lint"]
        )
        protection.required_status_checks = status_checks
    else:
        protection.required_status_checks = None
    protection.allow_force_pushes = allow_force_pushes
    protection.allow_deletions = allow_deletions
    return protection


def _patch_all_ok(
    project_dir: Path,
    *,
    oauth_scopes: list[str] | None = None,
    user_login: str = "testuser",
    repo_full_name: str = "owner/repo",
    default_branch: str = "main",
    protection: Mock | None = None,
) -> dict[str, object]:
    """Run verify_github with all dependencies mocked to succeed."""
    if oauth_scopes is None:
        oauth_scopes = ["repo", "workflow"]

    mock_user = Mock()
    mock_user.login = user_login

    mock_github_client = Mock()
    mock_github_client.get_user.return_value = mock_user
    mock_github_client.oauth_scopes = oauth_scopes

    mock_repo = Mock()
    mock_repo.full_name = repo_full_name

    mock_branch = Mock()
    if protection is None:
        protection = _make_mock_protection()
    mock_branch.get_protection.return_value = protection
    mock_repo.get_branch.return_value = mock_branch

    identifier = Mock()
    identifier.https_url = f"https://github.com/{repo_full_name}"

    with (
        patch(f"{MODULE}.get_github_token", return_value="ghp_testtoken"),
        patch(f"{MODULE}.Github", return_value=mock_github_client),
        patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
        patch(f"{MODULE}.BaseGitHubManager") as mock_manager_cls,
    ):
        mock_manager = Mock()
        mock_manager._get_repository.return_value = mock_repo
        mock_manager.get_default_branch.return_value = default_branch
        mock_manager_cls.return_value = mock_manager

        return verify_github(project_dir)


class TestAllConnectivityChecksPass:
    """Test that all connectivity checks pass with valid setup."""

    def test_overall_ok_true(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path)
        assert result["overall_ok"] is True

    def test_all_checks_ok(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path)
        for key in (
            "token_configured",
            "authenticated_user",
            "repo_url",
            "repo_accessible",
        ):
            check = result[key]
            assert isinstance(check, dict)
            assert check["ok"] is True

    def test_severity_is_error(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path)
        for key in (
            "token_configured",
            "authenticated_user",
            "repo_url",
            "repo_accessible",
        ):
            check = result[key]
            assert isinstance(check, dict)
            assert check["severity"] == "error"


class TestTokenNotConfigured:
    """Test behavior when GitHub token is not available."""

    def test_token_configured_fails(self, tmp_path: Path) -> None:
        mock_github_client = Mock()
        mock_github_client.get_user.side_effect = Exception("bad token")
        mock_github_client.oauth_scopes = None

        with (
            patch(f"{MODULE}.get_github_token", return_value=None),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=None),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_mgr_cls.side_effect = ValueError("no token")
            result = verify_github(tmp_path)

        check: CheckResult = result["token_configured"]  # type: ignore[assignment]
        assert check["ok"] is False
        assert result["overall_ok"] is False

    def test_overall_ok_false(self, tmp_path: Path) -> None:
        with (
            patch(f"{MODULE}.get_github_token", return_value=None),
            patch(f"{MODULE}.Github") as mock_gh,
            patch(f"{MODULE}.get_repository_identifier", return_value=None),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_gh.return_value.get_user.side_effect = Exception("no token")
            mock_gh.return_value.oauth_scopes = None
            mock_mgr_cls.side_effect = ValueError("no token")
            result = verify_github(tmp_path)

        assert result["overall_ok"] is False


class TestTokenConfiguredScopesReported:
    """Test that OAuth scopes are reported in the token check value."""

    def test_scopes_in_value(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path, oauth_scopes=["repo", "workflow"])
        check: CheckResult = result["token_configured"]  # type: ignore[assignment]
        assert "repo, workflow" in check["value"]

    def test_empty_scopes(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path, oauth_scopes=[])
        check: CheckResult = result["token_configured"]  # type: ignore[assignment]
        assert "none" in check["value"].lower() or check["value"].count("scopes") >= 1


class TestAuthFailure:
    """Test behavior when authentication fails."""

    def test_authenticated_user_fails(self, tmp_path: Path) -> None:
        mock_github_client = Mock()
        mock_github_client.get_user.side_effect = Exception("auth failed")
        mock_github_client.oauth_scopes = None

        identifier = Mock()
        identifier.https_url = "https://github.com/owner/repo"

        mock_repo = Mock()
        mock_repo.full_name = "owner/repo"
        mock_branch = Mock()
        mock_branch.get_protection.return_value = _make_mock_protection()
        mock_repo.get_branch.return_value = mock_branch

        with (
            patch(f"{MODULE}.get_github_token", return_value="ghp_test"),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_manager = Mock()
            mock_manager._get_repository.return_value = mock_repo
            mock_manager.get_default_branch.return_value = "main"
            mock_mgr_cls.return_value = mock_manager
            result = verify_github(tmp_path)

        check: CheckResult = result["authenticated_user"]  # type: ignore[assignment]
        assert check["ok"] is False
        assert result["overall_ok"] is False


class TestAuthFailureScopesUnknown:
    """Test that scopes are unknown when auth fails."""

    def test_scopes_unknown(self, tmp_path: Path) -> None:
        mock_github_client = Mock()
        mock_github_client.get_user.side_effect = Exception("auth failed")
        mock_github_client.oauth_scopes = None

        with (
            patch(f"{MODULE}.get_github_token", return_value="ghp_test"),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=None),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_mgr_cls.side_effect = ValueError("no token")
            result = verify_github(tmp_path)

        check: CheckResult = result["token_configured"]  # type: ignore[assignment]
        assert "unknown" in check["value"].lower()


class TestRepoUrlNotResolvable:
    """Test behavior when repository URL cannot be resolved."""

    def test_repo_url_fails(self, tmp_path: Path) -> None:
        mock_user = Mock()
        mock_user.login = "testuser"

        mock_github_client = Mock()
        mock_github_client.get_user.return_value = mock_user
        mock_github_client.oauth_scopes = ["repo"]

        with (
            patch(f"{MODULE}.get_github_token", return_value="ghp_test"),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=None),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_mgr_cls.side_effect = ValueError("no repo")
            result = verify_github(tmp_path)

        check: CheckResult = result["repo_url"]  # type: ignore[assignment]
        assert check["ok"] is False
        assert result["overall_ok"] is False


class TestRepoNotAccessible:
    """Test behavior when repository is not accessible."""

    def test_repo_accessible_fails(self, tmp_path: Path) -> None:
        mock_user = Mock()
        mock_user.login = "testuser"

        mock_github_client = Mock()
        mock_github_client.get_user.return_value = mock_user
        mock_github_client.oauth_scopes = ["repo"]

        identifier = Mock()
        identifier.https_url = "https://github.com/owner/repo"

        with (
            patch(f"{MODULE}.get_github_token", return_value="ghp_test"),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_manager = Mock()
            mock_manager._get_repository.return_value = None
            mock_mgr_cls.return_value = mock_manager
            result = verify_github(tmp_path)

        check: CheckResult = result["repo_accessible"]  # type: ignore[assignment]
        assert check["ok"] is False
        assert result["overall_ok"] is False


class TestChecksIndependence:
    """Test that checks run independently — failures don't prevent other checks."""

    def test_token_fails_others_still_run(self, tmp_path: Path) -> None:
        mock_github_client = Mock()
        mock_github_client.get_user.side_effect = Exception("no auth")
        mock_github_client.oauth_scopes = None

        with (
            patch(f"{MODULE}.get_github_token", return_value=None),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=None),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_mgr_cls.side_effect = ValueError("no token")
            result = verify_github(tmp_path)

        for key in (
            "token_configured",
            "authenticated_user",
            "repo_url",
            "repo_accessible",
        ):
            assert key in result

    def test_auth_fails_repo_checks_still_run(self, tmp_path: Path) -> None:
        mock_github_client = Mock()
        mock_github_client.get_user.side_effect = Exception("auth failed")
        mock_github_client.oauth_scopes = None

        identifier = Mock()
        identifier.https_url = "https://github.com/owner/repo"

        mock_repo = Mock()
        mock_repo.full_name = "owner/repo"
        mock_branch = Mock()
        mock_branch.get_protection.return_value = _make_mock_protection()
        mock_repo.get_branch.return_value = mock_branch

        with (
            patch(f"{MODULE}.get_github_token", return_value="ghp_test"),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_manager = Mock()
            mock_manager._get_repository.return_value = mock_repo
            mock_manager.get_default_branch.return_value = "main"
            mock_mgr_cls.return_value = mock_manager
            result = verify_github(tmp_path)

        # Auth failed but repo checks still ran
        assert result["authenticated_user"]["ok"] is False  # type: ignore[index]
        assert "repo_url" in result
        assert "repo_accessible" in result


# ===================================================================
# Branch protection checks (5–9)
# ===================================================================

BRANCH_CHECK_KEYS = (
    "branch_protection",
    "ci_checks_required",
    "strict_mode",
    "force_push",
    "branch_deletion",
)


class TestBranchProtectionAllPass:
    """Test all branch protection checks pass with full protection."""

    def test_all_five_checks_ok(self, tmp_path: Path) -> None:
        protection = _make_mock_protection(
            strict=True,
            contexts=["ci/test", "ci/lint"],
            allow_force_pushes=False,
            allow_deletions=False,
        )
        result = _patch_all_ok(tmp_path, protection=protection)
        for key in BRANCH_CHECK_KEYS:
            check: CheckResult = result[key]  # type: ignore[assignment]
            assert check["ok"] is True, f"{key} should be ok"
            assert check["severity"] == "warning"

    def test_overall_ok_true(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path)
        assert result["overall_ok"] is True


class TestNoBranchProtection404:
    """Test when get_protection() raises 404 — no protection configured."""

    def _run(self, tmp_path: Path) -> dict[str, object]:
        mock_user = Mock()
        mock_user.login = "testuser"

        mock_github_client = Mock()
        mock_github_client.get_user.return_value = mock_user
        mock_github_client.oauth_scopes = ["repo"]

        mock_branch = Mock()
        mock_branch.get_protection.side_effect = GithubException(
            status=404, data={"message": "Branch not protected"}, headers={}
        )

        mock_repo = Mock()
        mock_repo.full_name = "owner/repo"
        mock_repo.get_branch.return_value = mock_branch

        identifier = Mock()
        identifier.https_url = "https://github.com/owner/repo"

        with (
            patch(f"{MODULE}.get_github_token", return_value="ghp_test"),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_manager = Mock()
            mock_manager._get_repository.return_value = mock_repo
            mock_manager.get_default_branch.return_value = "main"
            mock_mgr_cls.return_value = mock_manager
            return verify_github(tmp_path)

    def test_all_five_not_ok(self, tmp_path: Path) -> None:
        result = self._run(tmp_path)
        for key in BRANCH_CHECK_KEYS:
            check: CheckResult = result[key]  # type: ignore[assignment]
            assert check["ok"] is False, f"{key} should not be ok"
            assert check["severity"] == "warning"

    def test_overall_ok_still_true(self, tmp_path: Path) -> None:
        result = self._run(tmp_path)
        assert result["overall_ok"] is True


class TestNoStatusChecksConfigured:
    """Test when required_status_checks is None."""

    def test_ci_checks_not_ok(self, tmp_path: Path) -> None:
        protection = _make_mock_protection(has_status_checks=False)
        result = _patch_all_ok(tmp_path, protection=protection)
        check: CheckResult = result["ci_checks_required"]  # type: ignore[assignment]
        assert check["ok"] is False

    def test_strict_mode_not_ok(self, tmp_path: Path) -> None:
        protection = _make_mock_protection(has_status_checks=False)
        result = _patch_all_ok(tmp_path, protection=protection)
        check: CheckResult = result["strict_mode"]  # type: ignore[assignment]
        assert check["ok"] is False


class TestStrictModeDisabled:
    """Test when strict mode is False."""

    def test_strict_mode_not_ok(self, tmp_path: Path) -> None:
        protection = _make_mock_protection(strict=False)
        result = _patch_all_ok(tmp_path, protection=protection)
        check: CheckResult = result["strict_mode"]  # type: ignore[assignment]
        assert check["ok"] is False
        assert "disabled" in check["value"].lower()


class TestForcePushEnabled:
    """Test when force push is allowed."""

    def test_force_push_not_ok(self, tmp_path: Path) -> None:
        protection = _make_mock_protection(allow_force_pushes=True)
        result = _patch_all_ok(tmp_path, protection=protection)
        check: CheckResult = result["force_push"]  # type: ignore[assignment]
        assert check["ok"] is False


class TestBranchDeletionEnabled:
    """Test when branch deletion is allowed."""

    def test_branch_deletion_not_ok(self, tmp_path: Path) -> None:
        protection = _make_mock_protection(allow_deletions=True)
        result = _patch_all_ok(tmp_path, protection=protection)
        check: CheckResult = result["branch_deletion"]  # type: ignore[assignment]
        assert check["ok"] is False


class TestBranchProtectionWhenRepoNotAccessible:
    """Test branch protection checks when repo is not accessible (check 4 failed)."""

    def test_all_five_present_and_not_ok(self, tmp_path: Path) -> None:
        mock_user = Mock()
        mock_user.login = "testuser"

        mock_github_client = Mock()
        mock_github_client.get_user.return_value = mock_user
        mock_github_client.oauth_scopes = ["repo"]

        identifier = Mock()
        identifier.https_url = "https://github.com/owner/repo"

        with (
            patch(f"{MODULE}.get_github_token", return_value="ghp_test"),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_manager = Mock()
            mock_manager._get_repository.return_value = None
            mock_mgr_cls.return_value = mock_manager
            result = verify_github(tmp_path)

        for key in BRANCH_CHECK_KEYS:
            check: CheckResult = result[key]  # type: ignore[assignment]
            assert check["ok"] is False
            assert "error" in check


class TestDefaultBranchNameInProtectionValue:
    """Test that the default branch name appears in protection check value."""

    def test_branch_name_in_value(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path, default_branch="develop")
        check: CheckResult = result["branch_protection"]  # type: ignore[assignment]
        assert "develop" in check["value"]


class TestOverallOkTrueWhenOnlyWarningsFail:
    """Test that overall_ok is True when only warning-severity checks fail."""

    def test_overall_ok_true_with_protection_failures(self, tmp_path: Path) -> None:
        protection = _make_mock_protection(
            strict=False,
            allow_force_pushes=True,
            allow_deletions=True,
            has_status_checks=False,
        )
        result = _patch_all_ok(tmp_path, protection=protection)
        # Branch protection found but all sub-checks fail
        assert result["overall_ok"] is True
