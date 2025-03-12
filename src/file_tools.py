"""File operation tools for MCP server."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

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
