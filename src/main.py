"""Main entry point for the MCP server."""

import argparse
import logging
import sys
from pathlib import Path

import structlog

# Import logging utilities
from src.log_utils import setup_logging

# Create loggers
stdlogger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="MCP File System Server")
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
        default="mcp_filesystem_server.log",
        help="Path for structured JSON logs (default: mcp_filesystem_server.log in current directory).",
    )
    parser.add_argument(
        "--console-only",
        action="store_true",
        help="Log only to console, ignore --log-file parameter.",
    )
    return parser.parse_args()


def main() -> None:
    """
    Main entry point for the MCP server.
    """
    # Parse command line arguments
    args = parse_args()

    # Configure logging
    log_file = None if args.console_only else args.log_file
    setup_logging(args.log_level, log_file)

    # Add debug logging after logger is initialized
    stdlogger.debug("Logger initialized in main")
    structured_logger.debug(
        "Structured logger initialized in main", log_level=args.log_level
    )

    # Import here to avoid circular imports (after logging is configured)
    from src.server import run_server

    # Validate project directory
    project_dir = Path(args.project_dir)
    if not project_dir.exists() or not project_dir.is_dir():
        stdlogger.error(
            f"Project directory does not exist or is not a directory: {project_dir}"
        )
        if log_file:
            structured_logger.error(
                "Invalid project directory",
                project_dir=str(project_dir),
                error="Directory does not exist or is not a directory",
            )
        sys.exit(1)

    # Convert to absolute path
    project_dir = project_dir.absolute()

    stdlogger.info(f"Starting MCP server with project directory: {project_dir}")
    if log_file:
        structured_logger.info(
            "Starting MCP server",
            project_dir=str(project_dir),
            log_level=args.log_level,
            log_file=log_file,
        )

    # Run the server with the project directory
    run_server(project_dir)


if __name__ == "__main__":
    main()
