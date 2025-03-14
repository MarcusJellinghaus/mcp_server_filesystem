"""Directory utilities for file operations."""

import logging
import os
from pathlib import Path
from typing import Optional, List, Union

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from .path_utils import get_project_dir, normalize_path

logger = logging.getLogger(__name__)


def _parse_gitignore_file(gitignore_path: Path, base_path: Path) -> List[str]:
    """
    Parse a gitignore file and normalize patterns relative to the base path.

    Args:
        gitignore_path: Path to the .gitignore file
        base_path: Base path to resolve relative patterns against

    Returns:
        List of normalized gitignore patterns
    """
    if not gitignore_path.is_file():
        return []

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            # Read lines, strip whitespace and comments
            raw_patterns = [
                line.strip() 
                for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        
        # Default ignore list
        patterns = [".git/"]

        # Process each pattern
        for pattern in raw_patterns:
            # Ignore empty patterns
            if not pattern:
                continue

            # Handle negation patterns
            if pattern.startswith('!'):
                # Negation patterns are more complex, for now we'll skip them
                continue

            # Normalize path separators
            pattern = pattern.replace('\\', '/')

            patterns.append(pattern)

        return patterns

    except IOError as e:
        logger.warning(f"Error reading gitignore file {gitignore_path}: {e}")
        return []


def _get_gitignore_spec(directory_path: Path) -> Optional[PathSpec]:
    """
    Get a PathSpec object by combining gitignore patterns from multiple sources.

    Args:
        directory_path: Absolute path to the directory

    Returns:
        A PathSpec object or None if no patterns found
    """
    # Get project directory
    project_dir = get_project_dir()

    # Collect patterns from different sources
    all_patterns = []

    # 1. Root project .gitignore
    root_gitignore = project_dir / ".gitignore"
    all_patterns.extend(_parse_gitignore_file(root_gitignore, project_dir))

    # 2. Local directory .gitignore
    local_gitignore = directory_path / ".gitignore"
    all_patterns.extend(_parse_gitignore_file(local_gitignore, directory_path))

    # Create PathSpec if we have patterns
    if all_patterns:
        try:
            return PathSpec.from_lines(GitWildMatchPattern, all_patterns)
        except Exception as e:
            logger.error(f"Error creating PathSpec: {e}")
            return None

    return None


def _discover_files(directory: Path) -> List[str]:
    """
    Discover all files in a directory recursively.

    Args:
        directory: Absolute path to the directory

    Returns:
        List of file paths relative to the project directory
    """
    project_dir = get_project_dir()
    
    discovered_files = []
    
    try:
        for root, _, files in os.walk(directory):
            root_path = Path(root)
            
            # Skip any directories that are not within the project
            try:
                rel_root = root_path.relative_to(project_dir)
            except ValueError:
                continue
            
            for file in files:
                # Construct full relative path
                rel_file_path = str(rel_root / file)
                discovered_files.append(rel_file_path)
        
        return discovered_files
    
    except Exception as e:
        logger.error(f"Error discovering files in {directory}: {e}")
        raise


def list_files(directory: Union[str, Path], use_gitignore: bool = True) -> List[str]:
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

    # Validate directory
    if not abs_path.exists():
        logger.error(f"Directory not found: {directory}")
        raise FileNotFoundError(f"Directory '{directory}' does not exist")

    if not abs_path.is_dir():
        logger.error(f"Path is not a directory: {directory}")
        raise NotADirectoryError(f"Path '{directory}' is not a directory")

    try:
        # Discover all files first
        all_files = _discover_files(abs_path)

        # If gitignore filtering is disabled, return all files
        if not use_gitignore:
            return all_files

        # Get gitignore spec
        spec = _get_gitignore_spec(abs_path)

        # If no spec, return all files
        if not spec:
            return all_files

        # Filter files based on gitignore patterns
        filtered_files = [
            file for file in all_files 
            if not spec.match_file(file) and not spec.match_file(f"{file}/")
        ]

        return filtered_files

    except Exception as e:
        logger.error(f"Error listing files in directory {rel_path}: {str(e)}")
        raise
