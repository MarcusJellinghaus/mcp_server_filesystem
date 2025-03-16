import logging
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

# Import utility functions from the main package
from src.file_tools import delete_file as delete_file_util
from src.file_tools import edit_file as edit_file_util
from src.file_tools import list_files as list_files_util
from src.file_tools import normalize_path
from src.file_tools import read_file as read_file_util
from src.file_tools import save_file as save_file_util

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create a FastMCP server instance
mcp = FastMCP("File System Service")

# Store the project directory as a module-level variable
_project_dir: Path = None


def set_project_dir(directory: Path) -> None:
    """Set the project directory for file operations.

    Args:
        directory: The project directory path
    """
    global _project_dir
    _project_dir = Path(directory)
    logger.info(f"Project directory set to: {_project_dir}")


@mcp.tool()
async def list_directory() -> List[str]:
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
async def save_file(file_path: str, content: str) -> bool:
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
async def delete_this_file(file_path: str) -> bool:
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
async def edit_file(
    path: str,
    edits: List[Dict[str, str]],
    dry_run: bool = False,
    options: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Make selective edits using advanced pattern matching and formatting.

    Features:
    - Line-based and multi-line content matching
    - Whitespace normalization with indentation preservation
    - Fuzzy matching with confidence scoring
    - Multiple simultaneous edits with correct positioning
    - Indentation style detection and preservation
    - Git-style diff output with context
    - Preview changes with dry run mode
    - Failed match debugging with confidence scores

    Args:
        path: File to edit
        edits: List of edit operations (each containing oldText and newText)
        dry_run: Preview changes without applying (default: False)
        options: Optional formatting settings
            - preserveIndentation: Keep existing indentation (default: True)
            - normalizeWhitespace: Normalize spaces while preserving structure (default: True)
            - partialMatch: Enable fuzzy matching (default: True)

    Returns:
        Detailed diff and match information for dry runs, otherwise applies changes
    """
    if not path or not isinstance(path, str):
        logger.error(f"Invalid file path parameter: {path}")
        raise ValueError(f"File path must be a non-empty string, got {type(path)}")

    if not isinstance(edits, list):
        logger.error(f"Invalid edits parameter: {edits}")
        raise ValueError(f"Edits must be a list, got {type(edits)}")

    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    # Ensure 'edits' objects use the correct keys
    normalized_edits = []
    for edit in edits:
        if not isinstance(edit, dict):
            raise ValueError(f"Each edit must be a dictionary, got {type(edit)}")

        # Map oldText/newText to old_text/new_text if needed
        normalized_edit = {}
        if "oldText" in edit:
            normalized_edit["old_text"] = edit["oldText"]
        elif "old_text" in edit:
            normalized_edit["old_text"] = edit["old_text"]
        else:
            raise ValueError("Each edit must contain 'oldText' or 'old_text'")

        if "newText" in edit:
            normalized_edit["new_text"] = edit["newText"]
        elif "new_text" in edit:
            normalized_edit["new_text"] = edit["new_text"]
        else:
            raise ValueError("Each edit must contain 'newText' or 'new_text'")

        normalized_edits.append(normalized_edit)

    # Normalize the options dictionary if provided
    normalized_options = {}
    if options:
        # Map camelCase to snake_case if needed
        if "preserveIndentation" in options:
            normalized_options["preserve_indentation"] = options["preserveIndentation"]
        elif "preserve_indentation" in options:
            normalized_options["preserve_indentation"] = options["preserve_indentation"]

        if "normalizeWhitespace" in options:
            normalized_options["normalize_whitespace"] = options["normalizeWhitespace"]
        elif "normalize_whitespace" in options:
            normalized_options["normalize_whitespace"] = options["normalize_whitespace"]

        if "partialMatch" in options:
            normalized_options["partial_match"] = options["partialMatch"]
        elif "partial_match" in options:
            normalized_options["partial_match"] = options["partial_match"]

        if "matchThreshold" in options:
            normalized_options["match_threshold"] = options["matchThreshold"]
        elif "match_threshold" in options:
            normalized_options["match_threshold"] = options["match_threshold"]

    logger.info(f"Editing file: {path}, dry_run: {dry_run}")

    try:
        # Normalize the path and call the utility function
        normalized_path = path

        result = edit_file_util(
            normalized_path,
            normalized_edits,
            dry_run=dry_run,
            options=normalized_options,
            project_dir=_project_dir,
        )

        return result
    except Exception as e:
        logger.error(f"Error editing file {path}: {str(e)}")
        raise


def run_server(project_dir: Path) -> None:
    """Run the MCP server with the given project directory.

    Args:
        project_dir: Path to the project directory
    """
    # Set the project directory
    set_project_dir(project_dir)

    # Run the server
    mcp.run()


# Run the server when the script is executed directly
if __name__ == "__main__":
    # The project directory should be set before running the server
    # This case is primarily for testing; in production, main.py should set it
    if _project_dir is None:
        raise RuntimeError(
            "Project directory not set. Please use set_project_dir() before running the server."
        )

    mcp.run()
