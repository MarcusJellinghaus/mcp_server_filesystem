"""File search utilities for glob matching and content searching."""

import fnmatch
from pathlib import Path
from typing import Any, Dict, Optional

from mcp_workspace.file_tools.directory_utils import list_files


def search_files(
    project_dir: Path,
    glob: Optional[str] = None,
    pattern: Optional[str] = None,
    context_lines: int = 0,
    max_results: int = 50,
    max_result_lines: int = 200,
) -> Dict[str, Any]:
    """Search file contents by regex and/or find files by glob pattern.

    Args:
        project_dir: Project root directory.
        glob: Glob pattern for file name matching (e.g. ``**/*.py``).
        pattern: Regex pattern for content searching (not implemented yet).
        context_lines: Number of context lines around matches.
        max_results: Maximum number of results to return.
        max_result_lines: Maximum total lines in result output.

    Returns:
        Dictionary with search results.

    Raises:
        ValueError: If neither glob nor pattern is provided.
    """
    if glob is None and pattern is None:
        raise ValueError("At least one of 'glob' or 'pattern' must be provided")

    all_files = list_files(".", project_dir=project_dir, use_gitignore=True)

    # File search mode: glob provided, no pattern
    if glob is not None:
        matched = [f for f in all_files if fnmatch.fnmatch(f, glob)]
    else:
        matched = all_files

    total = len(matched)
    truncated = total > max_results

    return {
        "mode": "file_search",
        "files": matched[:max_results],
        "total_files": total,
        "truncated": truncated,
    }
