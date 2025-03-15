"""Directory utilities for file operations."""

import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from .path_utils import get_project_dir, normalize_path

logger = logging.getLogger(__name__)


def _parse_gitignore_file(gitignore_path: Path, base_path: Path) -> List[str]:
    """Parse a gitignore file and normalize patterns."""
    if not gitignore_path.is_file():
        return []

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            raw_patterns = [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]

        patterns = [".git/"]
        for pattern in raw_patterns:
            if not pattern:
                continue
            pattern = pattern.replace("\\", "/")
            patterns.append(pattern)

        return patterns

    except IOError as e:
        logger.warning(f"Error reading gitignore file {gitignore_path}: {e}")
        return []


def _get_gitignore_spec(directory_path: Path) -> Optional[PathSpec]:
    """Get a PathSpec object combining gitignore patterns."""
    project_dir = get_project_dir()
    all_patterns = []

    root_gitignore = project_dir / ".gitignore"
    all_patterns.extend(_parse_gitignore_file(root_gitignore, project_dir))

    local_gitignore = directory_path / ".gitignore"
    all_patterns.extend(_parse_gitignore_file(local_gitignore, directory_path))

    if all_patterns:
        try:
            return PathSpec.from_lines(GitWildMatchPattern, all_patterns)
        except Exception as e:
            logger.error(f"Error creating PathSpec: {e}")
            return None

    return None


def _discover_files(directory: Path) -> List[str]:
    """Discover all files recursively."""
    project_dir = get_project_dir()
    discovered_files = []

    try:
        for root, _, files in os.walk(directory):
            root_path = Path(root)
            try:
                rel_root = root_path.relative_to(project_dir)
            except ValueError:
                continue

            for file in files:
                rel_file_path = str(rel_root / file)
                discovered_files.append(rel_file_path)

        return discovered_files

    except Exception as e:
        logger.error(f"Error discovering files in {directory}: {e}")
        raise


def filter_files_with_gitignore(
    files: List[str], gitignore_spec: Optional[PathSpec]
) -> List[str]:
    """
    Filter files based on gitignore patterns.

    Args:
        files: List of file paths to filter
        gitignore_spec: PathSpec object with gitignore patterns

    Returns:
        Filtered list of files not matching gitignore patterns
    """
    if not gitignore_spec:
        return files

    result = []
    
    for file_path in files:
        # Normalize path for consistent matching
        norm_path = file_path.replace("\\", "/")
        
        # Check if the file itself matches an ignore pattern
        if gitignore_spec.match_file(norm_path):
            continue
            
        # Check if it would match as a directory (with trailing slash)
        if not norm_path.endswith("/") and gitignore_spec.match_file(norm_path + "/"):
            continue
            
        # Check if any parent directory matches a pattern
        path_parts = norm_path.split("/")
        parent_matched = False
        for i in range(1, len(path_parts)):
            parent_path = "/".join(path_parts[:i])
            if gitignore_spec.match_file(parent_path) or gitignore_spec.match_file(parent_path + "/"):
                parent_matched = True
                break
                
        if parent_matched:
            continue
            
        # If not ignored, add to result
        result.append(file_path)
    
    return result


def list_files(directory: Union[str, Path], use_gitignore: bool = True) -> List[str]:
    """List all files in a directory and its subdirectories."""
    abs_path, rel_path = normalize_path(directory)

    if not abs_path.exists():
        logger.error(f"Directory not found: {directory}")
        raise FileNotFoundError(f"Directory '{directory}' does not exist")

    if not abs_path.is_dir():
        logger.error(f"Path is not a directory: {directory}")
        raise NotADirectoryError(f"Path '{directory}' is not a directory")

    try:
        all_files = _discover_files(abs_path)

        if not use_gitignore:
            return all_files

        spec = _get_gitignore_spec(abs_path)
        return filter_files_with_gitignore(all_files, spec)

    except Exception as e:
        logger.error(f"Error listing files in directory {rel_path}: {str(e)}")
        raise
