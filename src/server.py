import logging
import os
from pathlib import Path
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

# Import utility functions from file_tools
from src.file_tools import list_files as list_files_util
from src.file_tools import normalize_path
from src.file_tools import read_file as read_file_util
from src.file_tools import write_file as write_file_util

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create a FastMCP server instance
mcp = FastMCP("File System Service")


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
            "Project directory not set. Make sure to set the MCP_PROJECT_DIR environment variable."
        )
    return Path(project_dir)


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
    logger.info(f"Writing to file: {file_path}")
    try:
        success = write_file_util(file_path, content)
        return success
    except Exception as e:
        logger.error(f"Error writing to file: {str(e)}")
        raise


# Run the server when the script is executed directly
if __name__ == "__main__":
    mcp.run()
