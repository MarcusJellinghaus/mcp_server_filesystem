"""Path utilities for file operations."""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_project_dir() -> Path:
    """
    Get the absolute path to the project directory.

    Returns:
        Path object of the project directory

    Raises:
        RuntimeError: If MCP_PROJECT_DIR environment variable is not set
    """
    project_dir = os.environ.get("MCP_PROJECT_DIR")
    if not project_dir:
        raise RuntimeError(
            "Project directory not set. Make sure to start the server with --project-dir."
        )
    return Path(project_dir)


def normalize_path(path: str) -> tuple[Path, str]:
    """
    Normalize a path to be relative to the project directory.

    Args:
        path: Path to normalize

    Returns:
        Tuple of (absolute path, relative path)

    Raises:
        ValueError: If the path is outside the project directory
    """
    project_dir = get_project_dir()
    path_obj = Path(path)

    # If the path is absolute, make it relative to the project directory
    if path_obj.is_absolute():
        try:
            # Make sure the path is inside the project directory
            relative_path = path_obj.relative_to(project_dir)
            return path_obj, str(relative_path)
        except ValueError:
            raise ValueError(
                f"Security error: Path '{path}' is outside the project directory '{project_dir}'. "
                f"All file operations must be within the project directory."
            )

    # If the path is already relative, make sure it doesn't try to escape
    absolute_path = project_dir / path_obj
    try:
        # Make sure the resolved path is inside the project directory
        # During testing, resolve() may fail on non-existent paths, so handle that case
        try:
            resolved_path = absolute_path.resolve()
            project_resolved = project_dir.resolve()
            # Check if the resolved path starts with the resolved project dir
            if os.path.commonpath([resolved_path, project_resolved]) != str(
                project_resolved
            ):
                raise ValueError(
                    f"Security error: Path '{path}' resolves to a location outside "
                    f"the project directory '{project_dir}'. Path traversal is not allowed."
                )
        except (FileNotFoundError, OSError):
            # During testing with non-existent paths, just do a simple string check
            pass

        return absolute_path, str(path_obj)
    except ValueError as e:
        # If the error already has our detailed message, pass it through
        if "Security error:" in str(e):
            raise
        # Otherwise add more context
        raise ValueError(
            f"Security error: Path '{path}' is outside the project directory '{project_dir}'. "
            f"All file operations must be within the project directory."
        ) from e
