"""Directory utilities for file operations.

This module provides functions for file discovery and listing with gitignore support.
We use the external gitignore_parser library for handling .gitignore patterns.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from .gitignore_parser import parse_gitignore
from .path_utils import get_project_dir, normalize_path

logger = logging.getLogger(__name__)


def _discover_files(directory: Path) -> List[str]:
    """Discover all files recursively."""
    project_dir = get_project_dir()
    discovered_files = []

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


def filter_with_gitignore(file_paths: List[str], base_dir: Optional[Path] = None) -> List[str]:
    """Filter a list of file paths using .gitignore rules.
    
    Args:
        file_paths: List of file paths to filter
        base_dir: Directory containing the .gitignore file
        
    Returns:
        List of file paths that are not ignored
    """
    if base_dir is None:
        base_dir = get_project_dir()
    
    gitignore_path = base_dir / ".gitignore"
    if not gitignore_path.is_file():
        logger.info(f"No .gitignore file found in {base_dir}, skipping gitignore filtering")
        return file_paths
    
    try:
        # Read the gitignore file content for logging
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        logger.info(f"Gitignore content: {gitignore_content}")
        
        # Parse the gitignore file to get a matcher function
        logger.info(f"Parsing gitignore file at {gitignore_path}")
        matcher = parse_gitignore(gitignore_path)
        
        # Filter files using the matcher
        filtered_files = []
        project_dir = get_project_dir()
        
        for file_path in file_paths:
            # Convert to absolute path for the matcher
            abs_file_path = str(project_dir / file_path)
            logger.debug(f"Checking file: {file_path} (abs: {abs_file_path})")
            
            # The matcher returns True if the file should be ignored
            if not matcher(abs_file_path):
                logger.debug(f"Keeping file: {file_path}")
                filtered_files.append(file_path)
            else:
                logger.debug(f"Ignoring file: {file_path}")
        
        logger.info(f"Applied gitignore filtering: {len(file_paths)} files found, {len(filtered_files)} after filtering")
        return filtered_files
    except Exception as e:
        logger.warning(f"Error using gitignore parser, falling back to no filtering: {str(e)}")
        return file_paths


def list_files(directory: Union[str, Path], use_gitignore: bool = True) -> List[str]:
    """List all files in a directory and its subdirectories with optional gitignore filtering."""
    abs_path, rel_path = normalize_path(directory)

    if not abs_path.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")

    if not abs_path.is_dir():
        raise NotADirectoryError(f"Path '{directory}' is not a directory")

    try:
        all_files = _discover_files(abs_path)
        logger.info(f"Discovered {len(all_files)} files in {rel_path}")
        
        if not use_gitignore:
            return all_files
            
        # Apply gitignore filtering
        return filter_with_gitignore(all_files, abs_path)

    except Exception as e:
        logger.error(f"Error listing files in directory {rel_path}: {str(e)}")
        raise
