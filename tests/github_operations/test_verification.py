"""Unit tests for verify_github() connectivity and branch protection checks."""

from pathlib import Path
from typing import Literal
from unittest.mock import Mock, patch

from github.GithubException import GithubException

from mcp_workspace.github_operations.verification import CheckResult, verify_github

MODULE = "mcp_workspace.github_operations.verification"


def _make_identifier(
    hostname: str = "github.com",
    full_name: str = "owner/repo",
    api_base_url: str = "https://api.github.com",
) -> Mock:
    """Build a mock RepositoryIdentifier with explicit api_base_url."""
    m = Mock()
    m.https_url = f"https://{hostname}/{full_name}"
    m.api_base_url = api_base_url
    m.full_name = full_name
    return m


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
    delete_branch_on_merge: bool = True,
    token_source: Literal["env", "config"] = "env",
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
    mock_repo.delete_branch_on_merge = delete_branch_on_merge

    mock_branch = Mock()
    if protection is None:
        protection = _make_mock_protection()
    mock_branch.get_protection.return_value = protection
    mock_repo.get_branch.return_value = mock_branch

    identifier = _make_identifier(full_name=repo_full_name)

    with (
        patch(
            f"{MODULE}.get_github_token_with_source",
            return_value=("ghp_testtoken", token_source),
        ),
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
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=(None, None),
            ),
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
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=(None, None),
            ),
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

        identifier = _make_identifier()

        mock_repo = Mock()
        mock_repo.full_name = "owner/repo"
        mock_branch = Mock()
        mock_branch.get_protection.return_value = _make_mock_protection()
        mock_repo.get_branch.return_value = mock_branch

        with (
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=("ghp_test", "env"),
            ),
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
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=("ghp_test", "env"),
            ),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=None),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_mgr_cls.side_effect = ValueError("no token")
            result = verify_github(tmp_path)

        check: CheckResult = result["token_configured"]  # type: ignore[assignment]
        assert "unknown" in check["value"].lower()


class TestTokenSource:
    """Test that token_source is surfaced on token_configured."""

    def test_token_source_env(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path, token_source="env")
        check: CheckResult = result["token_configured"]  # type: ignore[assignment]
        assert check["token_source"] == "env"

    def test_token_source_config(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path, token_source="config")
        check: CheckResult = result["token_configured"]  # type: ignore[assignment]
        assert check["token_source"] == "config"

    def test_token_source_omitted_when_no_token(self, tmp_path: Path) -> None:
        mock_github_client = Mock()
        mock_github_client.get_user.side_effect = Exception("no token")
        mock_github_client.oauth_scopes = None

        with (
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=(None, None),
            ),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=None),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_mgr_cls.side_effect = ValueError("no token")
            result = verify_github(tmp_path)

        check: CheckResult = result["token_configured"]  # type: ignore[assignment]
        assert "token_source" not in check

    def test_token_source_set_on_auth_failure(self, tmp_path: Path) -> None:
        mock_github_client = Mock()
        mock_github_client.get_user.side_effect = Exception("Bad credentials")
        mock_github_client.oauth_scopes = None

        with (
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=("ghp_bad", "env"),
            ),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=None),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_mgr_cls.side_effect = ValueError("no repo")
            result = verify_github(tmp_path)

        auth_check: CheckResult = result["authenticated_user"]  # type: ignore[assignment]
        token_check: CheckResult = result["token_configured"]  # type: ignore[assignment]
        assert auth_check["ok"] is False
        assert token_check["token_source"] == "env"


class TestRepoUrlNotResolvable:
    """Test behavior when repository URL cannot be resolved."""

    def test_repo_url_fails(self, tmp_path: Path) -> None:
        mock_user = Mock()
        mock_user.login = "testuser"

        mock_github_client = Mock()
        mock_github_client.get_user.return_value = mock_user
        mock_github_client.oauth_scopes = ["repo"]

        with (
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=("ghp_test", "env"),
            ),
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

        identifier = _make_identifier()

        with (
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=("ghp_test", "env"),
            ),
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
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=(None, None),
            ),
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

        identifier = _make_identifier()

        mock_repo = Mock()
        mock_repo.full_name = "owner/repo"
        mock_branch = Mock()
        mock_branch.get_protection.return_value = _make_mock_protection()
        mock_repo.get_branch.return_value = mock_branch

        with (
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=("ghp_test", "env"),
            ),
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

        identifier = _make_identifier()

        with (
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=("ghp_test", "env"),
            ),
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

        identifier = _make_identifier()

        with (
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=("ghp_test", "env"),
            ),
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


# ===================================================================
# Check 10: auto_delete_branches
# ===================================================================


class TestAutoDeleteBranches:
    """Test auto_delete_branches check (check 10)."""

    def test_enabled(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path, delete_branch_on_merge=True)
        check: CheckResult = result["auto_delete_branches"]  # type: ignore[assignment]
        assert check["ok"] is True
        assert check["value"] == "auto-delete on merge"
        assert check["severity"] == "warning"

    def test_disabled(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path, delete_branch_on_merge=False)
        check: CheckResult = result["auto_delete_branches"]  # type: ignore[assignment]
        assert check["ok"] is False
        assert check["value"] == "not enabled"
        assert check["severity"] == "warning"

    def test_present_when_no_branch_protection(self, tmp_path: Path) -> None:
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
        mock_repo.delete_branch_on_merge = True

        identifier = _make_identifier()

        with (
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=("ghp_test", "env"),
            ),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_manager = Mock()
            mock_manager._get_repository.return_value = mock_repo
            mock_manager.get_default_branch.return_value = "main"
            mock_mgr_cls.return_value = mock_manager
            result = verify_github(tmp_path)

        check: CheckResult = result["auto_delete_branches"]  # type: ignore[assignment]
        assert check["ok"] is True
        assert check["value"] == "auto-delete on merge"

    def test_repo_not_accessible(self, tmp_path: Path) -> None:
        mock_user = Mock()
        mock_user.login = "testuser"

        mock_github_client = Mock()
        mock_github_client.get_user.return_value = mock_user
        mock_github_client.oauth_scopes = ["repo"]

        identifier = _make_identifier()

        with (
            patch(
                f"{MODULE}.get_github_token_with_source",
                return_value=("ghp_test", "env"),
            ),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_manager = Mock()
            mock_manager._get_repository.return_value = None
            mock_mgr_cls.return_value = mock_manager
            result = verify_github(tmp_path)

        check: CheckResult = result["auto_delete_branches"]  # type: ignore[assignment]
        assert check["ok"] is False
        assert check["value"] == "unknown"
        assert "error" in check


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



# ===================================================================
# Step 6: api_base_url result entry + auth probe base_url kwarg
# ===================================================================


def _patch_for_auth_probe(
    project_dir: Path,
    *,
    identifier: Mock | None,
) -> tuple[dict[str, object], Mock]:
    """Run verify_github and return (result, mock_github_class) for auth-probe assertions."""
    mock_user = Mock()
    mock_user.login = "testuser"

    mock_github_client = Mock()
    mock_github_client.get_user.return_value = mock_user
    mock_github_client.oauth_scopes = ["repo"]

    mock_repo = Mock()
    mock_repo.full_name = "owner/repo"
    mock_repo.delete_branch_on_merge = True
    mock_branch = Mock()
    mock_branch.get_protection.return_value = _make_mock_protection()
    mock_repo.get_branch.return_value = mock_branch

    with (
        patch(
            f"{MODULE}.get_github_token_with_source",
            return_value=("ghp_test", "env"),
        ),
        patch(f"{MODULE}.Github", return_value=mock_github_client) as mock_github_class,
        patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
        patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
    ):
        mock_manager = Mock()
        mock_manager._get_repository.return_value = mock_repo
        mock_manager.get_default_branch.return_value = "main"
        mock_mgr_cls.return_value = mock_manager
        result = verify_github(project_dir)

    return result, mock_github_class


class TestAuthProbeBaseUrlGithubCom:
    """Auth-probe Github(...) is called with base_url=https://api.github.com for github.com."""

    def test_base_url_is_github_com_api(self, tmp_path: Path) -> None:
        identifier = _make_identifier(
            hostname="github.com", api_base_url="https://api.github.com"
        )
        _, mock_github_class = _patch_for_auth_probe(tmp_path, identifier=identifier)
        assert mock_github_class.call_args.kwargs["base_url"] == "https://api.github.com"


class TestAuthProbeBaseUrlGhe:
    """Auth-probe is called with the GHE-tenant API URL when identifier is GHE."""

    def test_base_url_is_ghe_tenant(self, tmp_path: Path) -> None:
        identifier = _make_identifier(
            hostname="tenant.ghe.com",
            api_base_url="https://api.tenant.ghe.com",
        )
        _, mock_github_class = _patch_for_auth_probe(tmp_path, identifier=identifier)
        assert (
            mock_github_class.call_args.kwargs["base_url"]
            == "https://api.tenant.ghe.com"
        )

    def test_base_url_is_ghes(self, tmp_path: Path) -> None:
        identifier = _make_identifier(
            hostname="ghe.example.com",
            api_base_url="https://ghe.example.com/api/v3",
        )
        _, mock_github_class = _patch_for_auth_probe(tmp_path, identifier=identifier)
        assert (
            mock_github_class.call_args.kwargs["base_url"]
            == "https://ghe.example.com/api/v3"
        )


class TestAuthProbeBaseUrlFallback:
    """When identifier is None, auth probe falls back to api.github.com."""

    def test_base_url_fallback(self, tmp_path: Path) -> None:
        _, mock_github_class = _patch_for_auth_probe(tmp_path, identifier=None)
        assert mock_github_class.call_args.kwargs["base_url"] == "https://api.github.com"


class TestApiBaseUrlResultEntrySuccess:
    """result['api_base_url'] is ok=True with the identifier's API URL on success."""

    def test_success_shape(self, tmp_path: Path) -> None:
        identifier = _make_identifier(
            hostname="tenant.ghe.com",
            api_base_url="https://api.tenant.ghe.com",
        )
        result, _ = _patch_for_auth_probe(tmp_path, identifier=identifier)
        check: CheckResult = result["api_base_url"]  # type: ignore[assignment]
        assert check["ok"] is True
        assert check["value"] == "https://api.tenant.ghe.com"
        assert check["severity"] == "error"


class TestApiBaseUrlResultEntryFallback:
    """When identifier is None, api_base_url is a fallback warning entry."""

    def test_fallback_shape(self, tmp_path: Path) -> None:
        result, _ = _patch_for_auth_probe(tmp_path, identifier=None)
        check: CheckResult = result["api_base_url"]  # type: ignore[assignment]
        assert check["ok"] is False
        assert "fallback" in check["value"].lower()
        assert check["severity"] == "warning"
        assert "error" in check
        assert check["error"]


class TestApiBaseUrlIsFirstKey:
    """api_base_url must be the first key in the result dict."""

    def test_first_key_success(self, tmp_path: Path) -> None:
        identifier = _make_identifier()
        result, _ = _patch_for_auth_probe(tmp_path, identifier=identifier)
        assert next(iter(result.keys())) == "api_base_url"

    def test_first_key_fallback(self, tmp_path: Path) -> None:
        result, _ = _patch_for_auth_probe(tmp_path, identifier=None)
        assert next(iter(result.keys())) == "api_base_url"


class TestOverallOkNotPoisonedByFallback:
    """The api_base_url fallback (severity=warning) must NOT poison overall_ok by itself."""

    def test_fallback_alone_does_not_poison(self, tmp_path: Path) -> None:
        result, _ = _patch_for_auth_probe(tmp_path, identifier=None)

        # overall_ok IS False here, but the failure source is repo_url (severity=error),
        # not the api_base_url warning entry.
        assert result["overall_ok"] is False

        repo_url: CheckResult = result["repo_url"]  # type: ignore[assignment]
        assert repo_url["ok"] is False
        assert repo_url["severity"] == "error"

        api_base: CheckResult = result["api_base_url"]  # type: ignore[assignment]
        assert api_base["ok"] is False
        assert api_base["severity"] == "warning"
