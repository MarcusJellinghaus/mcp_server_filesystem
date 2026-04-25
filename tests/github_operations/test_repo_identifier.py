"""Tests for RepoIdentifier class."""

import pytest

from mcp_workspace.utils.repo_identifier import RepoIdentifier


class TestRepoIdentifierFromFullName:
    """Test RepoIdentifier.from_full_name() factory method."""

    def test_valid_owner_repo(self) -> None:
        """Test parsing valid 'owner/repo' format."""
        result = RepoIdentifier.from_full_name("owner/repo")
        assert result.owner == "owner"
        assert result.repo_name == "repo"

    def test_raises_on_no_slash(self) -> None:
        """Test ValueError for input without slash."""
        with pytest.raises(ValueError, match="Invalid repo identifier"):
            RepoIdentifier.from_full_name("just-repo")

    def test_raises_on_multiple_slashes(self) -> None:
        """Test ValueError for input with multiple slashes."""
        with pytest.raises(ValueError, match="Invalid repo identifier"):
            RepoIdentifier.from_full_name("a/b/c")

    def test_raises_on_empty_owner(self) -> None:
        """Test ValueError for '/repo' input."""
        with pytest.raises(ValueError, match="owner cannot be empty"):
            RepoIdentifier.from_full_name("/repo")

    def test_raises_on_empty_repo(self) -> None:
        """Test ValueError for 'owner/' input."""
        with pytest.raises(ValueError, match="repo_name cannot be empty"):
            RepoIdentifier.from_full_name("owner/")


class TestRepoIdentifierFromRepoUrl:
    """Test RepoIdentifier.from_repo_url() factory method."""

    def test_https_url(self) -> None:
        """Test parsing HTTPS GitHub URLs."""
        result = RepoIdentifier.from_repo_url("https://github.com/owner/repo")
        assert result.owner == "owner"
        assert result.repo_name == "repo"

    def test_https_url_with_git_suffix(self) -> None:
        """Test parsing HTTPS URLs with .git suffix."""
        result = RepoIdentifier.from_repo_url("https://github.com/owner/repo.git")
        assert result.owner == "owner"
        assert result.repo_name == "repo"

    def test_ssh_url(self) -> None:
        """Test parsing SSH GitHub URLs."""
        result = RepoIdentifier.from_repo_url("git@github.com:owner/repo")
        assert result.owner == "owner"
        assert result.repo_name == "repo"

    def test_ssh_url_with_git_suffix(self) -> None:
        """Test parsing SSH URLs with .git suffix."""
        result = RepoIdentifier.from_repo_url("git@github.com:owner/repo.git")
        assert result.owner == "owner"
        assert result.repo_name == "repo"

    def test_raises_on_invalid_url(self) -> None:
        """Test ValueError for invalid URLs."""
        with pytest.raises(ValueError, match="Invalid repository URL"):
            RepoIdentifier.from_repo_url("invalid")

    def test_non_github_url_succeeds(self) -> None:
        """Test that non-GitHub URLs are accepted (host-agnostic)."""
        result = RepoIdentifier.from_repo_url("https://gitlab.com/owner/repo")
        assert result.owner == "owner"
        assert result.repo_name == "repo"
        assert result.hostname == "gitlab.com"

    def test_raises_on_non_string(self) -> None:
        """Test ValueError for non-string input."""
        with pytest.raises(ValueError, match="Repository URL must be a string"):
            RepoIdentifier.from_repo_url(None)  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="Repository URL must be a string"):
            RepoIdentifier.from_repo_url(123)  # type: ignore[arg-type]


class TestRepoIdentifierProperties:
    """Test RepoIdentifier properties and methods."""

    def test_full_name_property(self) -> None:
        """Test full_name returns 'owner/repo' format."""
        repo = RepoIdentifier(owner="MarcusJellinghaus", repo_name="mcp_coder")
        assert repo.full_name == "MarcusJellinghaus/mcp_coder"

    def test_cache_safe_name_property(self) -> None:
        """Test cache_safe_name returns 'owner_repo' format."""
        repo = RepoIdentifier(owner="MarcusJellinghaus", repo_name="mcp_coder")
        assert repo.cache_safe_name == "MarcusJellinghaus_mcp_coder"

    def test_str_returns_full_name(self) -> None:
        """Test __str__ returns full_name format."""
        repo = RepoIdentifier(owner="owner", repo_name="repo")
        assert str(repo) == "owner/repo"
