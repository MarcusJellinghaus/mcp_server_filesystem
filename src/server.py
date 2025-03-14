import logging
import os
from pathlib import Path
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

# Import utility functions from the main package
from src.file_tools import (
    delete_file as delete_file_util,
    get_project_dir,
    list_files as list_files_util,
    normalize_path,
    read_file as read_file_util,
    write_file as write_file_util,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create a FastMCP server instance
mcp = FastMCP("File System Service")


@mcp.tool()
async def list_directory() -> List[str]:
    """List files and directories in the project directory.

    Returns:
        A list of filenames in the project directory
    """
    try:
        project_dir = get_project_dir()
        logger.info(f"Listing all files in project directory: {project_dir}")
        result = list_files_util(".", use_gitignore=True)
        return result
    except Exception as e:
        logger.error(f"Error listing project directory: {str(e)}")
        raise


@mcp.tool()
async def read_file(file_path: str) -> str:
    """Read the contents of a file.

    Args:
        file_path: Path to the file to read (relative to project directory)

    Returns:
        The contents of the file as a string
    """
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file path parameter: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")
        
    logger.info(f"Reading file: {file_path}")
    try:
        content = read_file_util(file_path)
        return content
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise


@mcp.tool()
async def write_file(file_path: str, content: str) -> bool:
    """Write content to a file.

    Args:
        file_path: Path to the file to write to (relative to project directory)
        content: Content to write to the file

    Returns:
        True if the file was written successfully
    """
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file path parameter: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")
        
    if content is None:
        logger.warning("Content is None, treating as empty string")
        content = ""
        
    if not isinstance(content, str):
        logger.error(f"Invalid content type: {type(content)}")
        raise ValueError(f"Content must be a string, got {type(content)}")
        
    logger.info(f"Writing to file: {file_path}")
    try:
        success = write_file_util(file_path, content)
        return success
    except Exception as e:
        logger.error(f"Error writing to file: {str(e)}")
        raise


@mcp.tool()
async def delete_file(file_path: str) -> bool:
    """Delete a specified file from the filesystem. This operation is irreversible and will permanently remove the file. Ensure that the correct file path is provided. Only works within allowed directories.

    Args:
        file_path: Path to the file to delete (relative to project directory)

    Returns:
        True if the file was deleted successfully
    """
    # Validate the file_path parameter
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file path parameter: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")
    
    logger.info(f"Deleting file: {file_path}")
    try:
        success = delete_file_util(file_path)
        logger.info(f"File deleted successfully: {file_path}")
        return success
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        raise


# Run the server when the script is executed directly
if __name__ == "__main__":
    mcp.run()
