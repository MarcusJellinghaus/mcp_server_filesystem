"""Shared fixtures for issue branch resolution tests."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_workspace.github_operations.issues import IssueBranchManager


@pytest.fixture
def mock_manager() -> IssueBranchManager:
    """Create a mock IssueBranchManager for testing."""
    mock_path = Mock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.is_dir.return_value = True

    with (
        patch("mcp_workspace.git_operations.is_git_repository", return_value=True),
        patch(
            "mcp_workspace.github_operations.base_manager.get_github_token",
            return_value="fake_token",
        ),
        patch("mcp_workspace.github_operations.base_manager.Github") as mock_github_cls,
    ):
        manager = IssueBranchManager(mock_path)
        # Set cached github client so lazy property doesn't trigger outside patch
        manager._cached_github_client = mock_github_cls.return_value
        return manager
