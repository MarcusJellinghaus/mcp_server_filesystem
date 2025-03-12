from mcp.server.fastmcp import FastMCP
import logging
import os
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create a FastMCP server instance
mcp = FastMCP("File System Service")

# Import utility functions from file_tools
from src.file_tools import (
    normalize_path,
    list_files as list_files_util,
    read_file as read_file_util,
    write_file as write_file_util
)

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
async def list_directory(directory: str, use_gitignore: bool = True) -> List[str]:
    """List files and directories in a specified directory.
    
    Args:
        directory: Path to the directory to list (relative to project directory)
        use_gitignore: Whether to filter results based on .gitignore patterns
    
    Returns:
        A list of filenames in the directory
    """
    logger.info(f"Listing directory: {directory}")
    try:
        result = list_files_util(directory, use_gitignore)
        return result
    except Exception as e:
        logger.error(f"Error listing directory: {str(e)}")
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

@mcp.tool()
async def check_path_exists(path: str) -> dict:
    """Check if a path exists and determine if it's a file or directory.
    
    Args:
        path: Path to check (relative to project directory)
    
    Returns:
        A dictionary with 'exists', 'is_file', and 'is_dir' properties
    """
    logger.info(f"Checking if path exists: {path}")
    try:
        abs_path, _ = normalize_path(path)
        exists = abs_path.exists()
        return {
            "exists": exists,
            "is_file": exists and abs_path.is_file(),
            "is_dir": exists and abs_path.is_dir()
        }
    except Exception as e:
        logger.error(f"Error checking path: {str(e)}")
        raise

@mcp.tool()
async def create_directory(directory: str) -> bool:
    """Create a directory and any necessary parent directories.
    
    Args:
        directory: Path of the directory to create (relative to project directory)
    
    Returns:
        True if the directory was created successfully
    """
    logger.info(f"Creating directory: {directory}")
    try:
        abs_path, _ = normalize_path(directory)
        if abs_path.exists():
            if not abs_path.is_dir():
                raise ValueError(f"Path exists but is not a directory: {directory}")
            return True  # Directory already exists
        
        abs_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Successfully created directory: {directory}")
        return True
    except Exception as e:
        logger.error(f"Error creating directory: {str(e)}")
        raise

@mcp.tool()
async def delete_file(file_path: str) -> bool:
    """Delete a file.
    
    Args:
        file_path: Path to the file to delete (relative to project directory)
    
    Returns:
        True if the file was deleted successfully
    """
    logger.info(f"Deleting file: {file_path}")
    try:
        abs_path, _ = normalize_path(file_path)
        if not abs_path.exists():
            logger.warning(f"File does not exist, nothing to delete: {file_path}")
            return False
        
        if not abs_path.is_file():
            raise ValueError(f"Path exists but is not a file: {file_path}")
        
        abs_path.unlink()
        logger.info(f"Successfully deleted file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise

# Run the server when the script is executed directly
if __name__ == "__main__":
    mcp.run()
