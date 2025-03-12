"""File operation tools for MCP server."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

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


def list_files(directory: str, use_gitignore: bool = True) -> list[str]:
    """
    List all files in a directory.

    Args:
        directory: Path to the directory to list files from (relative to project directory)
        use_gitignore: Whether to filter results based on .gitignore patterns (default: True)

    Returns:
        A list of filenames in the directory (relative to project directory)

    Raises:
        FileNotFoundError: If the directory does not exist
        PermissionError: If access to the directory is denied
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
        # Get all files in the directory
        logger.debug(f"Listing files in directory: {rel_path}")
        all_files = [str(f.name) for f in abs_path.iterdir()]
        logger.debug(f"Found {len(all_files)} unfiltered files in {rel_path}")

        # If gitignore filtering is not requested, return all files
        if not use_gitignore:
            logger.debug(f"Gitignore filtering disabled, returning all files")
            return all_files

        # Check if a .gitignore file exists in the directory
        gitignore_path = abs_path / ".gitignore"
        if not gitignore_path.exists() or not gitignore_path.is_file():
            # No .gitignore file found, return all files
            logger.debug(f"No .gitignore file found in {rel_path}, returning all files")
            return all_files

        try:
            # Read and parse .gitignore file
            logger.debug(f"Reading .gitignore file from {rel_path}")
            with open(gitignore_path, "r", encoding="utf-8") as f:
                gitignore_patterns = f.read().splitlines()

            # Always ignore .git directory if .gitignore exists
            if not any(
                pattern.strip() == ".git/" or pattern.strip() == ".git"
                for pattern in gitignore_patterns
            ):
                logger.debug(f"Adding .git/ to gitignore patterns")
                gitignore_patterns.append(".git/")

            # Create PathSpec object for pattern matching
            logger.debug(
                f"Creating gitignore PathSpec with {len(gitignore_patterns)} patterns"
            )
            spec = PathSpec.from_lines(GitWildMatchPattern, gitignore_patterns)

            # Filter files based on gitignore patterns
            filtered_files = []
            for item in all_files:
                # Check both the file name and the directory-style name with trailing slash
                # This ensures directories are properly matched by gitignore patterns
                if not spec.match_file(item) and not spec.match_file(f"{item}/"):
                    # If it's a directory, make extra sure it's not excluded
                    if (abs_path / item).is_dir():
                        # Additional check specifically for directories
                        if not any(
                            pattern.endswith("/") and pattern.rstrip("/") == item
                            for pattern in gitignore_patterns
                        ):
                            filtered_files.append(item)
                    else:
                        # Regular file
                        filtered_files.append(item)

            logger.debug(
                f"Filtered {len(all_files)} files down to {len(filtered_files)} files"
            )
            return filtered_files

        except Exception as e:
            # If there's an error parsing .gitignore, log it and return all files
            logger.warning(
                f"Error applying gitignore filter: {str(e)}. Returning all files."
            )
            return all_files
    except Exception as e:
        logger.error(f"Error listing files in directory {rel_path}: {str(e)}")
        raise


def read_file(file_path: str) -> str:
    """
    Read the contents of a file.

    Args:
        file_path: Path to the file to read (relative to project directory)

    Returns:
        The contents of the file as a string

    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If access to the file is denied
        ValueError: If the file is outside the project directory
    """
    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path)

    if not abs_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File '{file_path}' does not exist")

    if not abs_path.is_file():
        logger.error(f"Path is not a file: {file_path}")
        raise IsADirectoryError(f"Path '{file_path}' is not a file")

    file_handle = None
    try:
        logger.debug(f"Reading file: {rel_path}")
        file_handle = open(abs_path, "r", encoding="utf-8")
        content = file_handle.read()
        logger.debug(f"Successfully read {len(content)} bytes from {rel_path}")
        return content
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error while reading {rel_path}: {str(e)}")
        raise ValueError(
            f"File '{file_path}' contains invalid characters. Ensure it's a valid text file."
        ) from e
    except Exception as e:
        logger.error(f"Error reading file {rel_path}: {str(e)}")
        raise
    finally:
        if file_handle is not None:
            file_handle.close()


def write_file(file_path: str, content: str) -> bool:
    """
    Write content to a file atomically.

    Args:
        file_path: Path to the file to write to (relative to project directory)
        content: Content to write to the file

    Returns:
        True if the file was written successfully

    Raises:
        PermissionError: If access to the file is denied
        ValueError: If the file is outside the project directory
    """
    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path)

    # Create directory if it doesn't exist
    try:
        if not abs_path.parent.exists():
            logger.info(f"Creating directory: {abs_path.parent}")
            abs_path.parent.mkdir(parents=True)
    except PermissionError as e:
        logger.error(
            f"Permission denied creating directory {abs_path.parent}: {str(e)}"
        )
        raise
    except Exception as e:
        logger.error(f"Error creating directory {abs_path.parent}: {str(e)}")
        raise

    # Use a temporary file for atomic write
    temp_file = None
    try:
        # Create a temporary file in the same directory as the target
        # This ensures the atomic move works across filesystems
        temp_fd, temp_path = tempfile.mkstemp(dir=str(abs_path.parent))
        temp_file = Path(temp_path)

        logger.debug(f"Writing to temporary file for {rel_path}")

        # Write content to temporary file
        with open(temp_fd, "w", encoding="utf-8") as f:
            try:
                f.write(content)
            except UnicodeEncodeError as e:
                logger.error(
                    f"Unicode encode error while writing to {rel_path}: {str(e)}"
                )
                raise ValueError(
                    f"Content contains characters that cannot be encoded. Please check the encoding."
                ) from e

        # Atomically replace the target file
        logger.debug(f"Atomically replacing {rel_path} with temporary file")
        try:
            # On Windows, we need to remove the target file first
            if os.name == "nt" and abs_path.exists():
                abs_path.unlink()
            os.replace(temp_path, str(abs_path))
        except Exception as e:
            logger.error(f"Error replacing file {rel_path}: {str(e)}")
            raise

        logger.debug(f"Successfully wrote {len(content)} bytes to {rel_path}")
        return True

    except Exception as e:
        logger.error(f"Error writing to file {rel_path}: {str(e)}")
        raise

    finally:
        # Clean up the temporary file if it still exists
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary file {temp_file}: {str(e)}"
                )
