"""Main entry point for the MCP server."""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from mcp_workspace import __version__

# Import logging utilities
from mcp_workspace.log_utils import setup_logging

# Create loggers
stdlogger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="MCP File System Server - A Model Context Protocol server providing file operation tools"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mcp-workspace {__version__}",
        help="Show version number and exit",
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        required=True,
        help="Base directory for all file operations (required)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path for structured JSON logs (default: mcp_workspace_{timestamp}.log in project_dir/logs/).",
    )
    parser.add_argument(
        "--console-only",
        action="store_true",
        help="Log only to console, ignore --log-file parameter.",
    )
    parser.add_argument(
        "--reference-project",
        action="append",
        help="Reference project in format name=/path/to/dir (can be repeated)",
    )
    return parser.parse_args()


def validate_reference_projects(reference_args: List[str]) -> Dict[str, Path]:
    """Parse and validate reference project arguments.

    Validates name format (very permissive) and path existence. Logs warnings for invalid
    references and continues with valid ones only. Auto-renames duplicates.
    """
    if not reference_args:
        return {}

    validated_projects: Dict[str, Path] = {}

    for arg in reference_args:
        # Split on first '=' only
        if "=" not in arg:
            stdlogger.warning(
                "Invalid reference project format (missing '='): argument=%s, expected_format=name=/path/to/dir",
                arg,
            )
            continue

        name, path_str = arg.split("=", 1)

        # Validate name is not empty
        if not name:
            stdlogger.warning(
                "Invalid reference project format (empty name): argument=%s, expected_format=name=/path/to/dir",
                arg,
            )
            continue

        # Convert to absolute path
        project_path = Path(path_str).absolute()

        # Validate path exists and is directory
        if not project_path.exists():
            stdlogger.warning(
                "Reference project path does not exist: name=%s, path=%s",
                name,
                str(project_path),
            )
            continue

        if not project_path.is_dir():
            stdlogger.warning(
                "Reference project path is not a directory: name=%s, path=%s",
                name,
                str(project_path),
            )
            continue

        # Handle duplicate names with auto-rename
        final_name = name
        counter = 2
        while final_name in validated_projects:
            final_name = f"{name}_{counter}"
            counter += 1

        validated_projects[final_name] = project_path

    return validated_projects


def main() -> None:
    """
    Main entry point for the MCP server.
    """
    # Parse command line arguments
    args = parse_args()

    # Validate project directory first
    project_dir = Path(args.project_dir)
    if not project_dir.exists() or not project_dir.is_dir():
        print(
            f"Error: Project directory does not exist or is not a directory: {project_dir}"
        )
        sys.exit(1)

    # Convert to absolute path
    project_dir = project_dir.absolute()

    # Generate default log file path if not specified
    if args.console_only:
        log_file = None
    elif args.log_file:
        log_file = args.log_file
    else:
        # Create default log file in project_dir/logs/ with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logs_dir = project_dir / "logs"
        log_file = str(logs_dir / f"mcp_workspace_{timestamp}.log")

    # Configure logging now that we have the project directory
    setup_logging(args.log_level, log_file)

    # Add debug logging after logger is initialized
    stdlogger.debug("Logger initialized in main")

    # Parse reference projects
    reference_projects = {}
    if args.reference_project:
        reference_projects = validate_reference_projects(args.reference_project)

    # Import here to avoid circular imports (after logging is configured)
    from mcp_workspace.server import run_server

    stdlogger.debug(
        "Starting MCP server: project_dir=%s, log_level=%s, log_file=%s",
        project_dir,
        args.log_level,
        log_file,
    )

    # Run the server with the project directory and reference projects
    run_server(project_dir, reference_projects=reference_projects)


if __name__ == "__main__":
    main()
