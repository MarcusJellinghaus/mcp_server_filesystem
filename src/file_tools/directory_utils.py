"""Directory utilities for file operations."""

import logging
import os
from pathlib import Path
from typing import Optional

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from .path_utils import get_project_dir, normalize_path

logger = logging.getLogger(__name__)


def _get_gitignore_spec(directory_path: Path) -> Optional[PathSpec]:
    """
    Get a PathSpec object based on .gitignore files.

    Args:
        directory_path: Absolute path to the directory

    Returns:
        A PathSpec object or None if no patterns found
    """
    project_dir = get_project_dir()
    gitignore_patterns = [".git/"]  # Always ignore .git directory

    # Read the root .gitignore if it exists
    project_gitignore = project_dir / ".gitignore"
    if project_gitignore.exists() and project_gitignore.is_file():
        with open(project_gitignore, "r", encoding="utf-8") as f:
            gitignore_patterns.extend(f.read().splitlines())

    # Check if a local .gitignore file exists in the specified directory
    local_gitignore = directory_path / ".gitignore"
    if local_gitignore.exists() and local_gitignore.is_file():
        with open(local_gitignore, "r", encoding="utf-8") as f:
            gitignore_patterns.extend(f.read().splitlines())

    # Create PathSpec object for pattern matching if we have patterns
    if gitignore_patterns:
        return PathSpec.from_lines(GitWildMatchPattern, gitignore_patterns)

    return None


def list_files(directory: str, use_gitignore: bool = True) -> list[str]:
    """
    List all files in a directory and its subdirectories.

    Args:
        directory: Path to the directory to list files from (relative to project directory)
        use_gitignore: Whether to filter results based on .gitignore patterns (default: True)

    Returns:
        A list of filenames in the directory and subdirectories (relative to project directory)

    Raises:
        FileNotFoundError: If the directory does not exist
        NotADirectoryError: If the path is not a directory
        ValueError: If the directory is outside the project directory
    """
    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(directory)

    if not abs_path.exists():
        logger.error(f"Directory not found: {directory}")
        raise FileNotFoundError(f"Directory '{directory}' does not exist")

    if not abs_path.is_dir():
        logger.error(f"Path is not a directory: {directory}")
        raise NotADirectoryError(f"Path '{directory}' is not a directory")

    try:
        # Get gitignore spec if needed
        spec = None
        if use_gitignore:
            spec = _get_gitignore_spec(abs_path)

        # Collect all files recursively
        result_files = []
        project_dir = get_project_dir()

        for root, dirs, files in os.walk(abs_path):
            root_path = Path(root)
            rel_root = root_path.relative_to(project_dir)

            # Filter out ignored directories
            if spec:
                dirs_copy = dirs.copy()
                for d in dirs_copy:
                    check_path = str(rel_root / d)
                    if spec.match_file(check_path) or spec.match_file(f"{check_path}/"):
                        dirs.remove(d)

            # Add files that aren't ignored
            for file in files:
                rel_file_path = str(rel_root / file)

                if spec and spec.match_file(rel_file_path):
                    continue

                result_files.append(rel_file_path)

        return result_files

    except Exception as e:
        logger.error(f"Error listing files in directory {rel_path}: {str(e)}")
        raise
