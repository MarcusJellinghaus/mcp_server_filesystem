"""GitHub utility functions for URL parsing and validation.

This module provides utility functions for working with GitHub URLs and repositories.
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class RepoIdentifier:
    """Repository identifier with owner and repo name.

    Provides a single source of truth for repository identifier parsing.
    Use factory methods to create instances from different input formats.

    Attributes:
        owner: Repository owner (e.g., "MarcusJellinghaus")
        repo_name: Repository name (e.g., "mcp_coder")

    Properties:
        full_name: Returns "owner/repo" format
        cache_safe_name: Returns "owner_repo" format for filenames
    """

    owner: str
    repo_name: str

    @property
    def full_name(self) -> str:
        """Return repository in 'owner/repo' format."""
        return f"{self.owner}/{self.repo_name}"

    @property
    def cache_safe_name(self) -> str:
        """Return repository in 'owner_repo' format (safe for filenames)."""
        return f"{self.owner}_{self.repo_name}"

    def __str__(self) -> str:
        """Return string representation (full_name format)."""
        return self.full_name

    @classmethod
    def from_full_name(cls, full_name: str) -> "RepoIdentifier":
        """Parse 'owner/repo' format into RepoIdentifier.

        Args:
            full_name: Repository in "owner/repo" format

        Returns:
            RepoIdentifier instance

        Raises:
            ValueError: If input doesn't contain exactly one slash,
                       or if owner or repo_name is empty
        """
        slash_count = full_name.count("/")
        if slash_count != 1:
            raise ValueError(
                f"Invalid repo identifier '{full_name}': expected 'owner/repo' format "
                f"(exactly one slash), got {slash_count} slashes"
            )

        owner, repo_name = full_name.split("/")

        if not owner:
            raise ValueError(
                f"Invalid repo identifier '{full_name}': owner cannot be empty"
            )
        if not repo_name:
            raise ValueError(
                f"Invalid repo identifier '{full_name}': repo_name cannot be empty"
            )

        return cls(owner=owner, repo_name=repo_name)

    @classmethod
    def from_repo_url(cls, url: str) -> "RepoIdentifier":
        """Parse GitHub URL into RepoIdentifier.

        Supports both HTTPS and SSH URL formats:
        - https://github.com/owner/repo(.git)?
        - git@github.com:owner/repo(.git)?

        Args:
            url: GitHub repository URL

        Returns:
            RepoIdentifier instance

        Raises:
            ValueError: If URL is not a valid GitHub URL
        """
        if not isinstance(url, str):
            raise ValueError("Repository URL must be a string")

        # Pattern for HTTPS URLs: https://github.com/owner/repo(.git)?
        https_pattern = r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
        https_match = re.match(https_pattern, url)
        if https_match:
            owner, repo_name = https_match.groups()
            return cls.from_full_name(f"{owner}/{repo_name}")

        # Pattern for SSH URLs: git@github.com:owner/repo(.git)?
        ssh_pattern = r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?/?$"
        ssh_match = re.match(ssh_pattern, url)
        if ssh_match:
            owner, repo_name = ssh_match.groups()
            return cls.from_full_name(f"{owner}/{repo_name}")

        raise ValueError(f"Invalid GitHub URL '{url}': expected GitHub URL format")


def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """Parse GitHub URL and extract owner/repository name.

    Supports multiple GitHub URL formats:
    - HTTPS: https://github.com/owner/repo
    - HTTPS with .git: https://github.com/owner/repo.git
    - HTTPS with credentials: https://token@github.com/owner/repo.git
    - HTTPS with user:pass: https://user:pass@github.com/owner/repo.git
    - SSH: git@github.com:owner/repo.git
    - Short format: owner/repo

    Args:
        url: GitHub repository URL in various formats

    Returns:
        Tuple of (owner, repo_name) if valid GitHub URL, None otherwise

    Examples:
        >>> parse_github_url("https://github.com/user/repo")
        ('user', 'repo')
        >>> parse_github_url("https://token@github.com/user/repo.git")
        ('user', 'repo')
        >>> parse_github_url("git@github.com:user/repo.git")
        ('user', 'repo')
        >>> parse_github_url("user/repo")
        ('user', 'repo')
        >>> parse_github_url("invalid-url")
        None
    """
    if not isinstance(url, str) or not url.strip():
        return None

    # Pattern to match GitHub URLs in various formats
    # HTTPS: https://github.com/owner/repo(.git)?
    # HTTPS with credentials: https://[user[:pass]@]github.com/owner/repo(.git)?
    # SSH: git@github.com:owner/repo(.git)?
    # Short: owner/repo
    # The (?:[^@]+@)? part matches optional credentials (anything before @)
    github_pattern = r"(?:https://(?:[^@]+@)?github\.com/|git@github\.com:|^)([^/]+)/([^/\.]+)(?:\.git)?/?$"
    match = re.match(github_pattern, url.strip())

    if not match:
        return None

    owner, repo_name = match.groups()
    return owner, repo_name


def format_github_https_url(owner: str, repo_name: str) -> str:
    """Format owner/repo into standard GitHub HTTPS URL.

    Args:
        owner: Repository owner/organization name
        repo_name: Repository name

    Returns:
        Standard GitHub HTTPS URL

    Examples:
        >>> format_github_https_url("user", "repo")
        'https://github.com/user/repo'
    """
    return f"https://github.com/{owner}/{repo_name}"


def get_repo_full_name(url: str) -> Optional[str]:
    """Get repository full name (owner/repo) from GitHub URL.

    Args:
        url: GitHub repository URL in various formats

    Returns:
        Repository full name as "owner/repo" or None if invalid

    Examples:
        >>> get_repo_full_name("https://github.com/user/repo")
        'user/repo'
        >>> get_repo_full_name("git@github.com:user/repo.git")
        'user/repo'
        >>> get_repo_full_name("invalid-url")
        None
    """
    parsed = parse_github_url(url)
    if parsed is None:
        return None

    owner, repo_name = parsed
    return f"{owner}/{repo_name}"
