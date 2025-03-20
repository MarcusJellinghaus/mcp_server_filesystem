"""Directory utilities for file operations.

This module provides functions for file discovery and listing with gitignore support.
We use the external igittigitt library for handling .gitignore patterns.
"""

import logging
import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

from igittigitt import IgnoreParser

from .path_utils import normalize_path

logger = logging.getLogger(__name__)


def _discover_files(directory: Path, project_dir: Path) -> List[str]:
    """Discover all files recursively, excluding the .git directory."""
    discovered_files = []

    for root, dirs, files in os.walk(directory):
        # Skip .git directories
        if ".git" in dirs:
            dirs.remove(".git")

        root_path = Path(root)
        try:
            rel_root = root_path.relative_to(project_dir)
        except ValueError:
            continue

        for file in files:
            rel_file_path = str(rel_root / file)
            discovered_files.append(rel_file_path)

    return discovered_files


def read_gitignore_rules(
    gitignore_path: Path,
) -> Tuple[Optional[Callable], Optional[str]]:
    """Read and parse a .gitignore file to create a matcher function.

    Args:
        gitignore_path: Path to the .gitignore file

    Returns:
        A tuple containing (matcher_function, gitignore_content), or (None, None) if file doesn't exist
    """
    if not gitignore_path.is_file():
        logger.info(f"No .gitignore file found at {gitignore_path}")
        return None, None

    try:
        # Read the gitignore file content for logging
        with open(gitignore_path, "r") as f:
            gitignore_content = f.read()

        logger.info(f"Gitignore content: {gitignore_content}")

        # Parse the gitignore file to get a matcher function
        logger.info(f"Parsing gitignore file at {gitignore_path}")
        parser = IgnoreParser()
        parser.parse_rule_file(gitignore_path)

        # Create a matcher function that mimics the behavior of the old parse_gitignore
        def matcher(path):
            return parser.match(path)

        return matcher, gitignore_content

    except Exception as e:
        logger.warning(f"Error reading/parsing gitignore: {str(e)}")
        return None, None


def apply_gitignore_filter(
    file_paths: List[str], matcher: Callable, project_dir: Path
) -> List[str]:
    """Filter a list of file paths using a gitignore matcher function.

    Args:
        file_paths: List of file paths to filter
        matcher: Function that takes a path and returns True if it should be ignored
        project_dir: Base directory for resolving relative paths to absolute

    Returns:
        Filtered list of file paths that are not ignored
    """
    if matcher is None:
        return file_paths

    filtered_files = []

    # Validate project_dir parameter
    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    for file_path in file_paths:
        # Convert to absolute path for the matcher
        abs_file_path = str(project_dir / file_path)

        # The matcher returns True if the file should be ignored
        if not matcher(abs_file_path):
            filtered_files.append(file_path)

    logger.info(
        f"Applied gitignore filtering: {len(file_paths)} files found, {len(filtered_files)} after filtering"
    )
    return filtered_files


def filter_with_gitignore(
    file_paths: List[str], base_dir: Path, project_dir: Path
) -> List[str]:
    """Filter a list of file paths using .gitignore rules.

    Args:
        file_paths: List of file paths to filter
        base_dir: Directory containing the .gitignore file
        project_dir: Project directory path

    Returns:
        List of file paths that are not ignored
    """
    gitignore_path = base_dir / ".gitignore"

    # Get the matcher function from the gitignore file
    matcher, gitignore_content = read_gitignore_rules(gitignore_path)

    if matcher is None:
        return file_paths

    else:
        # Use the matcher for more complex gitignore patterns
        return apply_gitignore_filter(file_paths, matcher, project_dir)


def list_files(
    directory: Union[str, Path], project_dir: Path, use_gitignore: bool = True
) -> List[str]:
    """List all files in a directory and its subdirectories with optional gitignore filtering.

    Args:
        directory: Directory to list files from
        project_dir: Project directory path
        use_gitignore: Whether to apply gitignore filtering

    Returns:
        List of file paths
    """
    # Validate project_dir parameter
    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    abs_path, rel_path = normalize_path(directory, project_dir)

    if not abs_path.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")

    if not abs_path.is_dir():
        raise NotADirectoryError(f"Path '{directory}' is not a directory")

    try:
        all_files = _discover_files(abs_path, project_dir)
        logger.info(f"Discovered {len(all_files)} files in {rel_path}")

        if not use_gitignore:
            return all_files

        # Apply gitignore filtering
        return filter_with_gitignore(all_files, abs_path, project_dir)

    except Exception as e:
        logger.error(f"Error listing files in directory {rel_path}: {str(e)}")
        raise
