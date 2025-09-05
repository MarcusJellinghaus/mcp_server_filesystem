import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from mcp.server.fastmcp import FastMCP

# Import utility functions from the main package
from mcp_server_filesystem.file_tools import append_file as append_file_util
from mcp_server_filesystem.file_tools import delete_file as delete_file_util
from mcp_server_filesystem.file_tools import edit_file as edit_file_util
from mcp_server_filesystem.file_tools import list_files as list_files_util
from mcp_server_filesystem.file_tools import move_file as move_file_util
from mcp_server_filesystem.file_tools import normalize_path
from mcp_server_filesystem.file_tools import read_file as read_file_util
from mcp_server_filesystem.file_tools import save_file as save_file_util
from mcp_server_filesystem.log_utils import log_function_call

# Initialize loggers
logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)

# Create a FastMCP server instance
mcp = FastMCP("File System Service")

# Store the project directory as a module-level variable
_project_dir: Optional[Path] = None


@log_function_call
def set_project_dir(directory: Path) -> None:
    """Set the project directory for file operations.

    Args:
        directory: The project directory path
    """
    global _project_dir
    _project_dir = Path(directory)
    logger.info(f"Project directory set to: {_project_dir}")
    structured_logger.info("Project directory set", project_dir=str(_project_dir))


@mcp.tool()
@log_function_call
def list_directory() -> List[str]:
    """List files and directories in the project directory.

    Returns:
        A list of filenames in the project directory
    """
    try:
        if _project_dir is None:
            raise ValueError("Project directory has not been set")

        logger.info(f"Listing all files in project directory: {_project_dir}")
        # Explicitly pass project_dir to list_files_util
        result = list_files_util(".", project_dir=_project_dir, use_gitignore=True)
        return result
    except Exception as e:
        logger.error(f"Error listing project directory: {str(e)}")
        raise


@mcp.tool()
@log_function_call
def read_file(file_path: str) -> str:
    """Read the contents of a file.

    Args:
        file_path: Path to the file to read (relative to project directory)

    Returns:
        The contents of the file as a string
    """
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file path parameter: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    logger.info(f"Reading file: {file_path}")
    try:
        content = read_file_util(file_path, project_dir=_project_dir)
        return content
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise


@mcp.tool()
@log_function_call
def save_file(file_path: str, content: Any) -> bool:
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
    elif not isinstance(content, str):
        logger.error(f"Invalid content type: {type(content)}")
        raise ValueError(f"Content must be a string, got {type(content)}")

    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    logger.info(f"Writing to file: {file_path}")
    try:
        success = save_file_util(file_path, content, project_dir=_project_dir)
        return success
    except Exception as e:
        logger.error(f"Error writing to file: {str(e)}")
        raise


@mcp.tool()
@log_function_call
def append_file(file_path: str, content: Any) -> bool:
    """Append content to the end of a file.

    Args:
        file_path: Path to the file to append to (relative to project directory)
        content: Content to append to the file

    Returns:
        True if the content was appended successfully
    """
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file path parameter: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    if content is None:
        logger.warning("Content is None, treating as empty string")
        content = ""
    elif not isinstance(content, str):
        logger.error(f"Invalid content type: {type(content)}")
        raise ValueError(f"Content must be a string, got {type(content)}")

    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    logger.info(f"Appending to file: {file_path}")
    try:
        success = append_file_util(file_path, content, project_dir=_project_dir)
        return success
    except Exception as e:
        logger.error(f"Error appending to file: {str(e)}")
        raise


@mcp.tool()
@log_function_call
def delete_this_file(file_path: str) -> bool:
    """Delete a specified file from the filesystem.

    Args:
        file_path: Path to the file to delete (relative to project directory)

    Returns:
        True if the file was deleted successfully
    """
    # delete_file does not work with Claude Desktop (!!!)  ;-)
    # Validate the file_path parameter
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file path parameter: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    logger.info(f"Deleting file: {file_path}")
    try:
        # Directly delete the file without user confirmation
        success = delete_file_util(file_path, project_dir=_project_dir)
        logger.info(f"File deleted successfully: {file_path}")
        return success
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        raise


@mcp.tool()
@log_function_call
def move_file(source_path: str, destination_path: str) -> bool:
    """Move or rename a file or directory within the project.

    Args:
        source_path: Source file/directory path (relative to project)
        destination_path: Destination path (relative to project)

    Returns:
        True if successful

    Raises:
        ValueError: If inputs are invalid
        FileNotFoundError: If source doesn't exist
        FileExistsError: If destination already exists
    """
    # Validate inputs with simple error messages
    if not source_path or not isinstance(source_path, str):
        raise ValueError("Invalid source path")

    if not destination_path or not isinstance(destination_path, str):
        raise ValueError("Invalid destination path")

    if _project_dir is None:
        raise ValueError("Project directory not configured")

    try:
        # Call the underlying function (all logic is handled internally)
        result = move_file_util(source_path, destination_path, project_dir=_project_dir)

        # Return simple boolean
        return bool(result.get("success", False))

    except FileNotFoundError:
        # Simplify error message for LLM
        raise FileNotFoundError("File not found")
    except FileExistsError:
        # Simplify error message for LLM
        raise FileExistsError("Destination already exists")
    except PermissionError:
        # Simplify error message for LLM
        raise PermissionError("Permission denied")
    except ValueError as e:
        # For security errors, simplify the message
        if "Security" in str(e) or "outside" in str(e).lower():
            raise ValueError("Invalid path")
        raise ValueError("Invalid operation")
    except Exception as e:
        # Catch any other errors and simplify
        raise RuntimeError("Move operation failed") from e


@mcp.tool()
@log_function_call
def edit_file(
    file_path: str,
    edits: List[Dict[str, str]],
    dry_run: bool = False,
    options: Optional[Dict[str, bool]] = None,
) -> Dict[str, Any]:
    """Make selective edits to files using exact string matching.

    Features:
        - Exact string matching (no fuzzy matching)
        - Basic indentation preservation
        - First occurrence replacement only
        - Sequential edit processing
        - Already-applied edit detection
        - Git-style diff output with context
        - Preview changes with dry run mode

    Args:
        file_path: Path to the file to edit (relative to project directory)
        edits: List of edit operations (each containing old_text and new_text)
        dry_run: Preview changes without applying (default: False)
        options: Optional formatting settings
                            - preserve_indentation: Keep existing indentation (default: False)

    Returns:
        Dict containing:
            - success: bool indicating if all edits succeeded
            - diff: Git-style unified diff showing changes
            - match_results: List of results for each edit operation
            - file_path: Path of the edited file
            - dry_run: Whether this was a dry run
            - message: Optional status message
            - error: Error message if any edits failed
    """
    # Basic validation
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file path parameter: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    if not isinstance(edits, list) or not edits:
        logger.error(f"Invalid edits parameter: {edits}")
        raise ValueError("Edits must be a non-empty list")

    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    # Normalize edit operations (ensure proper format and required fields)
    normalized_edits = []
    for i, edit in enumerate(edits):
        if not isinstance(edit, dict):
            raise ValueError(f"Edit #{i} must be a dictionary, got {type(edit)}")

        # Validate required fields
        if "old_text" not in edit or "new_text" not in edit:
            missing = ", ".join([f for f in ["old_text", "new_text"] if f not in edit])
            raise ValueError(f"Edit #{i} is missing required field(s): {missing}")

        # Create normalized edit with just the fields we need
        normalized_edits.append(
            {"old_text": edit["old_text"], "new_text": edit["new_text"]}
        )

    # Process options (validate and only extract supported fields)
    normalized_options = {}
    supported_options = {"preserve_indentation"}

    if options:
        for opt_name, opt_value in options.items():
            if opt_name in supported_options:
                normalized_options[opt_name] = opt_value
            else:
                logger.warning(
                    f"Unsupported option '{opt_name}' ignored. Supported options: {supported_options}"
                )

    logger.info(f"Editing file: {file_path}, dry_run: {dry_run}")

    try:
        # Call the implementation function
        return edit_file_util(
            file_path,  # Already normalized by path_utils in the utility function
            normalized_edits,
            dry_run=dry_run,
            options=normalized_options,
            project_dir=_project_dir,
        )
    except Exception as e:
        logger.error(f"Error editing file {file_path}: {str(e)}")
        raise


@log_function_call
def run_server(project_dir: Path) -> None:
    """Run the MCP server with the given project directory.

    Args:
        project_dir: Path to the project directory
    """
    logger.debug("Entering run_server function")
    structured_logger.debug(
        "Entering run_server function", project_dir=str(project_dir)
    )

    # Set the project directory
    set_project_dir(project_dir)

    # Run the server
    logger.info("Starting MCP server")
    structured_logger.info("Starting MCP server")
    logger.debug("About to call mcp.run()")
    structured_logger.debug("About to call mcp.run()", project_dir=str(project_dir))
    mcp.run()
    logger.debug(
        "After mcp.run() call - this line will only execute if mcp.run() returns"
    )
