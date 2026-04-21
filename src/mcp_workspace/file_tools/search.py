"""File search utilities for glob matching and content searching."""

import fnmatch
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_workspace.file_tools.directory_utils import list_files
from mcp_workspace.file_tools.path_utils import normalize_path


def _search_content(
    files: List[str],
    compiled: "re.Pattern[str]",
    project_dir: Path,
    context_lines: int,
    max_results: int,
    max_result_lines: int,
) -> Dict[str, Any]:
    """Search file contents for regex matches.

    Returns content_search result dict.
    """
    matches: List[Dict[str, Any]] = []
    total_matches = 0
    total_lines_so_far = 0
    truncated = False

    for rel_path in files:
        abs_path, _ = normalize_path(rel_path, project_dir)
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                file_lines = f.readlines()
        except UnicodeDecodeError:
            continue

        for i, line in enumerate(file_lines):
            if not compiled.search(line):
                continue

            total_matches += 1

            # Check if we've already hit the caps for returned matches
            if truncated:
                continue

            start = max(0, i - context_lines)
            end = min(len(file_lines), i + context_lines + 1)
            context = "".join(file_lines[start:end]).rstrip("\n")
            match_lines = context.count("\n") + 1

            if (
                len(matches) >= max_results
                or total_lines_so_far + match_lines > max_result_lines
            ):
                truncated = True
                continue

            matches.append({"file": rel_path, "line": i + 1, "text": context})
            total_lines_so_far += match_lines

    return {
        "mode": "content_search",
        "details": matches,
        "total_matches": total_matches,
        "truncated": truncated,
    }


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
        pattern: Regex pattern for content searching.
        context_lines: Number of context lines around matches.
        max_results: Maximum number of results to return.
        max_result_lines: Maximum total lines in result output.

    Returns:
        Dictionary with search results.

    Raises:
        ValueError: If neither glob nor pattern is provided, or if
            pattern is an invalid regex.
    """
    if glob is None and pattern is None:
        raise ValueError("At least one of 'glob' or 'pattern' must be provided")

    all_files = list_files(".", project_dir=project_dir, use_gitignore=True)

    if glob is not None:
        matched = [f for f in all_files if fnmatch.fnmatch(f, glob)]
    else:
        matched = all_files

    # Content search mode: pattern provided
    if pattern is not None:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {exc}") from exc

        return _search_content(
            matched,
            compiled,
            project_dir,
            context_lines,
            max_results,
            max_result_lines,
        )

    # File search mode: glob only
    total = len(matched)
    truncated = total > max_results

    return {
        "mode": "file_search",
        "files": matched[:max_results],
        "total_files": total,
        "truncated": truncated,
    }
