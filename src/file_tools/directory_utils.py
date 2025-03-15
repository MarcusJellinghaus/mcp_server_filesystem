"""Directory utilities for file operations.

This module provides functions for file discovery and listing with gitignore support.
We use the external gitignore_parser library for handling .gitignore patterns.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Union, Callable

from .path_utils import get_project_dir, normalize_path
from .gitignore_parser import parse_gitignore

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


def list_files(directory: Union[str, Path], use_gitignore: bool = True) -> List[str]:
    """List all files in a directory and its subdirectories with optional gitignore filtering."""
    abs_path, rel_path = normalize_path(directory)

    if not abs_path.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")

    if not abs_path.is_dir():
        raise NotADirectoryError(f"Path '{directory}' is not a directory")

    try:
        all_files = _discover_files(abs_path)

        if not use_gitignore:
            return all_files

        # Check for .gitignore file
        gitignore_path = abs_path / ".gitignore"
        if not gitignore_path.is_file():
            return all_files

        # Use the external gitignore_parser
        try:
            matcher = parse_gitignore(gitignore_path)
            
            # External gitignore_parser expects absolute paths
            filtered_files = []
            for file_path in all_files:
                # Convert to absolute path for the matcher
                abs_file_path = str(get_project_dir() / file_path)
                
                # gitignore_parser returns True if the file should be ignored
                if not matcher(abs_file_path):
                    filtered_files.append(file_path)
                    
            return filtered_files
        except Exception as e:
            logger.warning(f"Error using gitignore parser, falling back to no filtering: {e}")
            return all_files

    except Exception as e:
        logger.error(f"Error listing files in directory {rel_path}: {str(e)}")
        raise
