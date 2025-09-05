"""File operations utilities."""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from git import Repo
from git.exc import GitCommandError

from mcp_server_filesystem.file_tools.git_operations import (
    is_file_tracked,
    is_git_repository,
)
from mcp_server_filesystem.file_tools.path_utils import normalize_path
from mcp_server_filesystem.log_utils import log_function_call

logger = logging.getLogger(__name__)


def read_file(file_path: str, project_dir: Path) -> str:
    """
    Read the contents of a file.

    Args:
        file_path: Path to the file to read (relative to project directory)
        project_dir: Project directory path

    Returns:
        The contents of the file as a string

    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If access to the file is denied
        ValueError: If the file is outside the project directory
    """
    # Validate file_path parameter
    if not file_path or not isinstance(file_path, str):
        logger.error("Invalid file path: %s", file_path)
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    # Validate project_dir parameter
    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path, project_dir)

    if not abs_path.exists():
        logger.error("File not found: %s", file_path)
        raise FileNotFoundError(f"File '{file_path}' does not exist")

    if not abs_path.is_file():
        logger.error("Path is not a file: %s", file_path)
        raise IsADirectoryError(f"Path '{file_path}' is not a file")

    file_handle = None
    try:
        logger.debug("Reading file: %s", rel_path)
        file_handle = open(abs_path, "r", encoding="utf-8")
        content = file_handle.read()
        logger.debug("Successfully read %s bytes from %s", len(content), rel_path)
        return content
    except UnicodeDecodeError as e:
        logger.error("Unicode decode error while reading %s: %s", rel_path, str(e))
        raise ValueError(
            f"File '{file_path}' contains invalid characters. Ensure it's a valid text file."
        ) from e
    except Exception as e:
        logger.error("Error reading file %s: %s", rel_path, str(e))
        raise
    finally:
        if file_handle is not None:
            file_handle.close()


def save_file(file_path: str, content: Any, project_dir: Path) -> bool:
    """
    Write content to a file atomically.

    Args:
        file_path: Path to the file to write to (relative to project directory)
        content: Content to write to the file
        project_dir: Project directory path

    Returns:
        True if the file was written successfully

    Raises:
        PermissionError: If access to the file is denied
        ValueError: If the file is outside the project directory
    """
    # Validate file_path parameter
    if not file_path or not isinstance(file_path, str):
        logger.error("Invalid file path: %s", file_path)
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    # Validate content parameter
    if content is None:
        logger.warning("Content is None, treating as empty string")
        content = ""
    elif not isinstance(content, str):
        logger.error("Invalid content type: %s", type(content))
        raise ValueError(f"Content must be a string, got {type(content)}")

    # Validate project_dir parameter
    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path, project_dir)

    # Create directory if it doesn't exist
    try:
        if not abs_path.parent.exists():
            logger.info("Creating directory: %s", abs_path.parent)
            abs_path.parent.mkdir(parents=True)
    except PermissionError as e:
        logger.error(
            "Permission denied creating directory %s: %s", abs_path.parent, str(e)
        )
        raise
    except Exception as e:
        logger.error("Error creating directory %s: %s", abs_path.parent, str(e))
        raise

    # Use a temporary file for atomic write
    temp_file = None
    try:
        # Create a temporary file in the same directory as the target
        # This ensures the atomic move works across filesystems
        temp_fd, temp_path = tempfile.mkstemp(dir=str(abs_path.parent))
        temp_file = Path(temp_path)

        logger.debug("Writing to temporary file for %s", rel_path)

        # Write content to temporary file
        with open(temp_fd, "w", encoding="utf-8") as f:
            try:
                f.write(content)
            except UnicodeEncodeError as e:
                logger.error(
                    "Unicode encode error while writing to %s: %s", rel_path, str(e)
                )
                raise ValueError(
                    "Content contains characters that cannot be encoded. Please check the encoding."
                ) from e

        # Atomically replace the target file
        logger.debug("Atomically replacing %s with temporary file", rel_path)
        try:
            # On Windows, we need to remove the target file first
            if os.name == "nt" and abs_path.exists():
                abs_path.unlink()
            os.replace(temp_path, str(abs_path))
        except Exception as e:
            logger.error("Error replacing file %s: %s", rel_path, str(e))
            raise

        logger.debug("Successfully wrote %s bytes to %s", len(content), rel_path)
        return True

    finally:
        # Clean up the temporary file if it still exists
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning(
                    "Failed to clean up temporary file %s: %s", temp_file, str(e)
                )


# Keep write_file for backward compatibility
write_file = save_file


def append_file(file_path: str, content: Any, project_dir: Path) -> bool:
    """
    Append content to the end of a file.

    Args:
        file_path: Path to the file to append to (relative to project directory)
        content: Content to append to the file
        project_dir: Project directory path

    Returns:
        True if the content was appended successfully

    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If access to the file is denied
        ValueError: If the file is outside the project directory
    """
    # Validate file_path parameter
    if not file_path or not isinstance(file_path, str):
        logger.error("Invalid file path: %s", file_path)
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    # Validate content parameter
    if content is None:
        logger.warning("Content is None, treating as empty string")
        content = ""
    elif not isinstance(content, str):
        logger.error("Invalid content type: %s", type(content))
        raise ValueError(f"Content must be a string, got {type(content)}")

    # Validate project_dir parameter
    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path, project_dir)

    # Check if the file exists
    if not abs_path.exists():
        logger.error("File not found: %s", file_path)
        raise FileNotFoundError(f"File '{file_path}' does not exist")

    if not abs_path.is_file():
        logger.error("Path is not a file: %s", file_path)
        raise IsADirectoryError(f"Path '{file_path}' is not a file")

    # Read existing content
    existing_content = read_file(file_path, project_dir)

    # Append new content
    combined_content = existing_content + content

    # Use save_file to write the combined content
    logger.debug("Appending %s bytes to %s", len(content), rel_path)
    return save_file(file_path, combined_content, project_dir)


def delete_file(file_path: str, project_dir: Path) -> bool:
    """
    Delete a file.

    Args:
        file_path: Path to the file to delete (relative to project directory)
        project_dir: Project directory path

    Returns:
        True if the file was deleted successfully

    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If access to the file is denied
        IsADirectoryError: If the path points to a directory
        ValueError: If the file is outside the project directory or the parameter is invalid
    """
    # Validate file_path parameter
    if not file_path or not isinstance(file_path, str):
        logger.error("Invalid file path: %s", file_path)
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    # Validate project_dir parameter
    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path, project_dir)

    if not abs_path.exists():
        logger.error("File not found: %s", file_path)
        raise FileNotFoundError(f"File '{file_path}' does not exist")

    if not abs_path.is_file():
        logger.error("Path is not a file: %s", file_path)
        raise IsADirectoryError(f"Path '{file_path}' is not a file or is a directory")

    try:
        logger.debug("Deleting file: %s", rel_path)
        abs_path.unlink()
        logger.debug("Successfully deleted file: %s", rel_path)
        return True
    except PermissionError as e:
        logger.error("Permission denied when deleting file %s: %s", rel_path, str(e))
        raise
    except Exception as e:
        logger.error("Error deleting file %s: %s", rel_path, str(e))
        raise


@log_function_call  # Automatic logging of parameters, timing, and exceptions
def move_file(
    source_path: str, destination_path: str, project_dir: Path
) -> Dict[str, Any]:
    """
    Move or rename a file or directory.

    Automatically uses git mv if the file is tracked by git,
    otherwise uses standard filesystem operations.
    Always creates parent directories if they don't exist.

    Args:
        source_path: Source file/directory path (relative to project_dir)
        destination_path: Destination path (relative to project_dir)
        project_dir: Project directory path

    Returns:
        Dict containing:
            - success: bool indicating if the move succeeded
            - method: 'git' or 'filesystem' indicating method used
            - source: normalized source path
            - destination: normalized destination path
            - message: optional status message

    Raises:
        FileNotFoundError: If source doesn't exist
        FileExistsError: If destination already exists
        ValueError: If paths are invalid or outside project directory
        PermissionError: If lacking permissions for the operation
    """
    # Validate inputs
    if not source_path or not isinstance(source_path, str):
        raise ValueError(
            f"Source path must be a non-empty string, got {type(source_path)}"
        )

    if not destination_path or not isinstance(destination_path, str):
        raise ValueError(
            f"Destination path must be a non-empty string, got {type(destination_path)}"
        )

    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    # Normalize paths (this also validates they're within project_dir)
    src_abs, src_rel = normalize_path(source_path, project_dir)
    dest_abs, dest_rel = normalize_path(destination_path, project_dir)

    # Check if source exists
    if not src_abs.exists():
        raise FileNotFoundError(f"Source file '{source_path}' does not exist")

    # Check if destination already exists
    if dest_abs.exists():
        raise FileExistsError(f"Destination '{destination_path}' already exists")

    # Automatically create parent directories
    dest_parent = dest_abs.parent
    dest_parent.mkdir(parents=True, exist_ok=True)

    # Automatically determine if git should be used
    should_use_git = False
    if is_git_repository(project_dir):
        # Simply check if the source is tracked (for files)
        # For directories, git mv will handle it or fail gracefully
        if src_abs.is_file():
            should_use_git = is_file_tracked(src_abs, project_dir)
        else:
            # For directories, just try git mv and let it fail if needed
            should_use_git = True

    # Try git move if applicable
    if should_use_git:
        try:
            logger.info("Attempting git move: %s -> %s", src_rel, dest_rel)
            logger.debug("Moving %s to %s using git mv", src_rel, dest_rel)

            repo = Repo(project_dir, search_parent_directories=False)

            # Convert paths to posix format for git (even on Windows)
            git_src = src_rel.replace("\\", "/")
            git_dest = dest_rel.replace("\\", "/")

            # Execute git mv
            repo.git.mv(git_src, git_dest)

            logger.info("Successfully moved using git: %s -> %s", src_rel, dest_rel)

            return {
                "success": True,
                "method": "git",
                "source": src_rel,
                "destination": dest_rel,
                "message": "File moved using git mv (preserving history)",
            }

        except (GitCommandError, Exception) as e:
            logger.warning(
                "Git move failed for %s, falling back to filesystem: %s", src_rel, e
            )
            # Fall through to filesystem move

    # Use filesystem operations (either as primary method or fallback)
    try:
        logger.debug("Moving %s to %s using filesystem operations", src_rel, dest_rel)

        # Use shutil.move for both files and directories
        shutil.move(str(src_abs), str(dest_abs))

        message = "File moved using filesystem operations"
        if should_use_git:
            message += " (fallback from git)"

        logger.info("Successfully moved: %s -> %s", src_rel, dest_rel)

        return {
            "success": True,
            "method": "filesystem",
            "source": src_rel,
            "destination": dest_rel,
            "message": message,
        }

    except PermissionError as e:
        logger.error("Permission denied moving %s to %s: %s", src_rel, dest_rel, e)
        raise
    except Exception as e:
        logger.error("Error moving %s to %s: %s", src_rel, dest_rel, e)
        raise
