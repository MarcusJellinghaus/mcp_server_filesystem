"""File operations utilities."""

import logging
import os
import tempfile
from pathlib import Path

from .path_utils import normalize_path

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
        logger.error(f"Invalid file path: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    # Validate project_dir parameter
    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path, project_dir)

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


def save_file(file_path: str, content: str, project_dir: Path) -> bool:
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
        logger.error(f"Invalid file path: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    # Validate content parameter
    if content is None:
        logger.warning("Content is None, treating as empty string")
        content = ""

    if not isinstance(content, str):
        logger.error(f"Invalid content type: {type(content)}")
        raise ValueError(f"Content must be a string, got {type(content)}")

    # Validate project_dir parameter
    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path, project_dir)

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


# Keep write_file for backward compatibility
write_file = save_file


def append_file(file_path: str, content: str, project_dir: Path) -> bool:
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
        logger.error(f"Invalid file path: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    # Validate content parameter
    if content is None:
        logger.warning("Content is None, treating as empty string")
        content = ""

    if not isinstance(content, str):
        logger.error(f"Invalid content type: {type(content)}")
        raise ValueError(f"Content must be a string, got {type(content)}")

    # Validate project_dir parameter
    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path, project_dir)

    # Check if the file exists
    if not abs_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File '{file_path}' does not exist")

    if not abs_path.is_file():
        logger.error(f"Path is not a file: {file_path}")
        raise IsADirectoryError(f"Path '{file_path}' is not a file")

    try:
        # Read existing content
        existing_content = read_file(file_path, project_dir)

        # Append new content
        combined_content = existing_content + content

        # Use save_file to write the combined content
        logger.debug(f"Appending {len(content)} bytes to {rel_path}")
        return save_file(file_path, combined_content, project_dir)

    except Exception as e:
        logger.error(f"Error appending to file {rel_path}: {str(e)}")
        raise


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
        logger.error(f"Invalid file path: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    # Validate project_dir parameter
    if project_dir is None:
        raise ValueError("Project directory cannot be None")

    # Normalize the path to be relative to the project directory
    abs_path, rel_path = normalize_path(file_path, project_dir)

    if not abs_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File '{file_path}' does not exist")

    if not abs_path.is_file():
        logger.error(f"Path is not a file: {file_path}")
        raise IsADirectoryError(f"Path '{file_path}' is not a file or is a directory")

    try:
        logger.debug(f"Deleting file: {rel_path}")
        abs_path.unlink()
        logger.debug(f"Successfully deleted file: {rel_path}")
        return True
    except PermissionError as e:
        logger.error(f"Permission denied when deleting file {rel_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error deleting file {rel_path}: {str(e)}")
        raise
