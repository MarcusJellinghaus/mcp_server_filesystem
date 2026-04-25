"""Unit tests for verify_github() connectivity checks (1–4)."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_workspace.github_operations.verification import CheckResult, verify_github

MODULE = "mcp_workspace.github_operations.verification"


@pytest.fixture
def _mock_git_repo(tmp_path: Path) -> Path:
    """Return tmp_path after patching is_git_repository to accept it."""
    return tmp_path


def _patch_all_ok(
    project_dir: Path,
    *,
    oauth_scopes: list[str] | None = None,
    user_login: str = "testuser",
    repo_full_name: str = "owner/repo",
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
        mock_manager_cls.return_value = mock_manager

        return verify_github(project_dir)


class TestAllConnectivityChecksPass:
    """Test that all connectivity checks pass with valid setup."""

    def test_overall_ok_true(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path)
        assert result["overall_ok"] is True

    def test_all_checks_ok(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path)
        for key in ("token_configured", "authenticated_user", "repo_url", "repo_accessible"):
            check = result[key]
            assert isinstance(check, dict)
            assert check["ok"] is True

    def test_severity_is_error(self, tmp_path: Path) -> None:
        result = _patch_all_ok(tmp_path)
        for key in ("token_configured", "authenticated_user", "repo_url", "repo_accessible"):
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

        with (
            patch(f"{MODULE}.get_github_token", return_value="ghp_test"),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_manager = Mock()
            mock_manager._get_repository.return_value = mock_repo
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

        for key in ("token_configured", "authenticated_user", "repo_url", "repo_accessible"):
            assert key in result

    def test_auth_fails_repo_checks_still_run(self, tmp_path: Path) -> None:
        mock_github_client = Mock()
        mock_github_client.get_user.side_effect = Exception("auth failed")
        mock_github_client.oauth_scopes = None

        identifier = Mock()
        identifier.https_url = "https://github.com/owner/repo"

        mock_repo = Mock()
        mock_repo.full_name = "owner/repo"

        with (
            patch(f"{MODULE}.get_github_token", return_value="ghp_test"),
            patch(f"{MODULE}.Github", return_value=mock_github_client),
            patch(f"{MODULE}.get_repository_identifier", return_value=identifier),
            patch(f"{MODULE}.BaseGitHubManager") as mock_mgr_cls,
        ):
            mock_manager = Mock()
            mock_manager._get_repository.return_value = mock_repo
            mock_mgr_cls.return_value = mock_manager
            result = verify_github(tmp_path)

        # Auth failed but repo checks still ran
        assert result["authenticated_user"]["ok"] is False  # type: ignore[index]
        assert "repo_url" in result
        assert "repo_accessible" in result
