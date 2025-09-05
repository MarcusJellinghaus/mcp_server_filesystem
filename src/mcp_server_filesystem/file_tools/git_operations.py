"""Git operations utilities for file system operations."""

import logging
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

# Use same logging pattern as existing modules (see file_operations.py)
logger = logging.getLogger(__name__)


def is_git_repository(project_dir: Path) -> bool:
    """
    Check if the project directory is a git repository.

    Args:
        project_dir: Path to check for git repository

    Returns:
        True if the directory is a git repository, False otherwise
    """
    logger.debug(f"Checking if {project_dir} is a git repository")

    try:
        Repo(project_dir, search_parent_directories=False)
        logger.debug(f"Detected as git repository: {project_dir}")
        return True
    except InvalidGitRepositoryError:
        logger.debug(f"Not a git repository: {project_dir}")
        return False
    except Exception as e:
        logger.warning(f"Error checking if directory is git repository: {e}")
        return False


def is_file_tracked(file_path: Path, project_dir: Path) -> bool:
    """
    Check if a file is tracked by git.

    Args:
        file_path: Path to the file to check
        project_dir: Project directory containing the git repository

    Returns:
        True if the file is tracked by git, False otherwise
    """
    if not is_git_repository(project_dir):
        return False

    try:
        repo = Repo(project_dir, search_parent_directories=False)

        # Get relative path from project directory
        try:
            relative_path = file_path.relative_to(project_dir)
        except ValueError:
            # File is outside project directory
            logger.debug(f"File {file_path} is outside project directory {project_dir}")
            return False

        # Convert to posix path for git (even on Windows)
        git_path = str(relative_path).replace("\\", "/")

        # Check if file is in the index (staged) or committed
        # This is more accurate than just using ls-files
        try:
            # Try to get the file from the index
            _ = repo.odb.stream(repo.index.entries[(git_path, 0)].binsha)
            return True
        except (KeyError, AttributeError):
            # File not in index, check if it's in committed files
            pass

        # Get list of tracked files using ls-files
        tracked_files = repo.git.ls_files().split("\n") if repo.git.ls_files() else []

        return git_path in tracked_files

    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug(f"Git error checking if file is tracked: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking if file is tracked: {e}")
        return False


def git_move(source_path: Path, dest_path: Path, project_dir: Path) -> bool:
    """
    Move a file using git mv command.

    Args:
        source_path: Source file path
        dest_path: Destination file path
        project_dir: Project directory containing the git repository

    Returns:
        True if the file was moved successfully using git, False otherwise

    Raises:
        GitCommandError: If git mv command fails
    """
    if not is_git_repository(project_dir):
        return False

    try:
        repo = Repo(project_dir, search_parent_directories=False)

        # Get relative paths from project directory
        try:
            source_relative = source_path.relative_to(project_dir)
            dest_relative = dest_path.relative_to(project_dir)
        except ValueError as e:
            logger.error(f"Paths must be within project directory: {e}")
            return False

        # Convert to posix paths for git
        source_git = str(source_relative).replace("\\", "/")
        dest_git = str(dest_relative).replace("\\", "/")

        # Execute git mv command
        logger.info(f"Executing git mv from {source_git} to {dest_git}")
        repo.git.mv(source_git, dest_git)

        logger.info(
            f"Successfully moved file using git from {source_git} to {dest_git}"
        )
        return True

    except GitCommandError as e:
        logger.error(f"Git move failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during git move: {e}")
        return False
