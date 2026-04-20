import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp_coder_utils.log_utils import log_function_call

# Import utility functions from the main package
from mcp_workspace.file_tools import append_file as append_file_util
from mcp_workspace.file_tools import delete_file as delete_file_util
from mcp_workspace.file_tools import edit_file as edit_file_util
from mcp_workspace.file_tools import list_files as list_files_util
from mcp_workspace.file_tools import move_file as move_file_util
from mcp_workspace.file_tools import normalize_path
from mcp_workspace.file_tools import read_file as read_file_util
from mcp_workspace.file_tools import save_file as save_file_util
from mcp_workspace.file_tools import search_files as search_files_util
from mcp_workspace.file_tools.directory_utils import is_path_gitignored
from mcp_workspace.git_operations.read_operations import git as git_impl
from mcp_workspace.reference_projects import ReferenceProject
from mcp_workspace.server_reference_tools import register as register_reference_tools
from mcp_workspace.server_reference_tools import set_reference_projects

# Initialize loggers
logger = logging.getLogger(__name__)

# Create a FastMCP server instance
mcp = FastMCP("File System Service")
register_reference_tools(mcp)

# Store the project directory as a module-level variable
_project_dir: Optional[Path] = None


def _check_not_gitignored(file_path: str) -> None:
    """Raise ValueError if path is excluded by .gitignore.

    This is a security boundary — always enforced, no toggle.
    """
    if _project_dir is None:
        return  # Can't check without project_dir; other validation will catch this
    # Normalize to relative path for gitignore checking
    path = Path(file_path)
    if path.is_absolute():
        try:
            file_path = str(path.relative_to(_project_dir))
        except ValueError:
            return  # Path outside project dir — other validation handles this
    if is_path_gitignored(file_path, _project_dir):
        raise ValueError(
            f"File '{file_path}' is excluded by .gitignore and cannot be accessed. "
            "Use list_directory() to see available files."
        )


@log_function_call
def set_project_dir(directory: Path) -> None:
    """Set the project directory for file operations.

    Args:
        directory: The project directory path
    """
    global _project_dir  # pylint: disable=global-statement
    _project_dir = Path(directory)
    logger.info("Project directory set to: %s", _project_dir)


@mcp.tool()
@log_function_call
def search_files(
    glob: Optional[str] = None,
    pattern: Optional[str] = None,
    context_lines: int = 0,
    max_results: int = 50,
    max_result_lines: int = 200,
) -> Dict[str, Any]:
    """Search file contents by regex and/or find files by glob pattern.

    Modes:
        - File search: provide `glob` to find files by path pattern (like find)
        - Content search: provide `pattern` (regex) to search inside files (like grep)
        - Combined: both to search content within matching files

    Args:
        glob: File path pattern (e.g. "**/*.py", "tests/**/test_*.py")
        pattern: Regex to match file contents (e.g. "def foo", "TODO.*fix")
        context_lines: Lines of context around each match (0 = match line only)
        max_results: Maximum number of matches or files returned (default 50)
        max_result_lines: Hard cap on total output lines (default 200)

    Returns:
        Dict with matches (content search) or file list (file search),
        plus truncated flag if results were capped.
    """
    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    return search_files_util(
        project_dir=_project_dir,
        glob=glob,
        pattern=pattern,
        context_lines=context_lines,
        max_results=max_results,
        max_result_lines=max_result_lines,
    )


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

        logger.info("Listing all files in project directory: %s", _project_dir)
        # Explicitly pass project_dir to list_files_util
        result = list_files_util(".", project_dir=_project_dir, use_gitignore=True)
        return result
    except Exception as e:
        logger.error("Error listing project directory: %s", str(e))
        raise


@mcp.tool()
@log_function_call
def read_file(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    with_line_numbers: Optional[bool] = None,
) -> str:
    """Read the contents of a file.

    Args:
        file_path: Path to the file to read (relative to project directory)
        start_line: First line to return (1-based, inclusive). Requires end_line.
        end_line: Last line to return (1-based, inclusive). Requires start_line.
        with_line_numbers: Prefix lines with line numbers. Defaults to True for
            sliced reads, False for full reads.

    Returns:
        The contents of the file as a string
    """
    if not file_path or not isinstance(file_path, str):
        logger.error("Invalid file path parameter: %s", file_path)
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    _check_not_gitignored(file_path)

    logger.info("Reading file: %s", file_path)
    try:
        content = read_file_util(
            file_path,
            project_dir=_project_dir,
            start_line=start_line,
            end_line=end_line,
            with_line_numbers=with_line_numbers,
        )
        return content
    except Exception as e:
        logger.error("Error reading file: %s", str(e))
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
        logger.error("Invalid file path parameter: %s", file_path)
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    if content is None:
        logger.warning("Content is None, treating as empty string")
        content = ""
    elif not isinstance(content, str):
        logger.error("Invalid content type: %s", type(content))
        raise ValueError(f"Content must be a string, got {type(content)}")

    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    _check_not_gitignored(file_path)

    logger.info("Writing to file: %s", file_path)
    try:
        success = save_file_util(file_path, content, project_dir=_project_dir)
        return success
    except Exception as e:
        logger.error("Error writing to file: %s", str(e))
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
        logger.error("Invalid file path parameter: %s", file_path)
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    if content is None:
        logger.warning("Content is None, treating as empty string")
        content = ""
    elif not isinstance(content, str):
        logger.error("Invalid content type: %s", type(content))
        raise ValueError(f"Content must be a string, got {type(content)}")

    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    _check_not_gitignored(file_path)

    logger.info("Appending to file: %s", file_path)
    try:
        success = append_file_util(file_path, content, project_dir=_project_dir)
        return success
    except Exception as e:
        logger.error("Error appending to file: %s", str(e))
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
        logger.error("Invalid file path parameter: %s", file_path)
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    _check_not_gitignored(file_path)

    logger.info("Deleting file: %s", file_path)
    try:
        # Directly delete the file without user confirmation
        success = delete_file_util(file_path, project_dir=_project_dir)
        logger.info("File deleted successfully: %s", file_path)
        return success
    except Exception as e:
        logger.error("Error deleting file %s: %s", file_path, str(e))
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

    _check_not_gitignored(source_path)
    _check_not_gitignored(destination_path)

    try:
        # Call the underlying function (all logic is handled internally)
        result = move_file_util(source_path, destination_path, project_dir=_project_dir)

        # Return simple boolean
        return bool(result.get("success", False))

    except FileNotFoundError as exc:
        # Simplify error message for LLM
        raise FileNotFoundError("File not found") from exc
    except FileExistsError as exc:
        # Simplify error message for LLM
        raise FileExistsError("Destination already exists") from exc
    except PermissionError as exc:
        # Simplify error message for LLM
        raise PermissionError("Permission denied") from exc
    except ValueError as e:
        # For security errors, simplify the message
        if "Security" in str(e) or "outside" in str(e).lower():
            raise ValueError("Invalid path") from e
        raise ValueError("Invalid operation") from e
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
        logger.error("Invalid file path parameter: %s", file_path)
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    if not isinstance(edits, list) or not edits:
        logger.error("Invalid edits parameter: %s", edits)
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
                    "Unsupported option '%s' ignored. Supported options: %s",
                    opt_name,
                    supported_options,
                )

    _check_not_gitignored(file_path)

    logger.info("Editing file: %s, dry_run: %s", file_path, dry_run)

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
        logger.error("Error editing file %s: %s", file_path, str(e))
        raise


@mcp.tool()
@log_function_call
def git(
    command: str,
    args: Optional[List[str]] = None,
    pathspec: Optional[List[str]] = None,
    search: Optional[str] = None,
    context: int = 3,
    max_lines: Optional[int] = None,
    compact: bool = True,
) -> str:
    """Run a read-only git command.

    Args:
        command: Git subcommand (log, diff, status, merge_base, fetch,
            show, branch, rev_parse, ls_tree, ls_files, ls_remote).
        args: Optional CLI flags (validated against per-command security allowlists).
        pathspec: Optional file paths appended after --.
        search: Optional regex to filter output (log, diff, show only).
        context: Lines of context around search matches (default 3).
        max_lines: Maximum output lines. Per-command defaults: log=50, diff=100, status=200, others=100.
        compact: If True, apply compact diff rendering (diff, show only).

    Returns:
        Command output, optionally filtered/truncated.
    """
    if _project_dir is None:
        raise ValueError("Project directory has not been set")
    return git_impl(
        command=command,
        project_dir=_project_dir,
        args=args,
        pathspec=pathspec,
        search=search,
        context=context,
        max_lines=max_lines,
        compact=compact,
    )


@log_function_call
def run_server(
    project_dir: Path,
    reference_projects: Optional[Dict[str, ReferenceProject]] = None,
) -> None:
    """Run the MCP server with the given project directory and optional reference projects.

    Args:
        project_dir: Path to the project directory
        reference_projects: Optional dictionary mapping project names to directory paths
    """
    logger.debug("Entering run_server function")

    # Set the project directory
    set_project_dir(project_dir)

    # Set reference projects if provided
    if reference_projects:
        set_reference_projects(reference_projects)

    # Run the server
    logger.info("Starting MCP server")
    logger.debug("About to call mcp.run()")
    mcp.run()
    logger.debug(
        "After mcp.run() call - this line will only execute if mcp.run() returns"
    )
