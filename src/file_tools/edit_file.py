import difflib
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .path_utils import normalize_path

logger = logging.getLogger(__name__)


@dataclass
class EditOperation:
    """Represents a single edit operation."""

    old_text: str
    new_text: str


@dataclass
class EditOptions:
    """Optional formatting settings for edit operations."""

    preserve_indentation: bool = True
    normalize_whitespace: bool = True


class MatchResult:
    """Stores information about a match attempt."""

    def __init__(
        self,
        matched: bool,
        line_index: int = -1,
        line_count: int = 0,
        details: str = "",
    ):
        self.matched = matched
        self.line_index = line_index
        self.line_count = line_count
        self.details = details

    def __repr__(self) -> str:
        return (
            f"MatchResult(matched={self.matched}, "
            f"line_index={self.line_index}, line_count={self.line_count})"
        )


def normalize_line_endings(text: str) -> str:
    """Convert all line endings to Unix style (\n)."""
    return text.replace("\r\n", "\n")


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace while preserving overall structure."""
    # Collapse multiple spaces into one
    result = re.sub(r"[ \t]+", " ", text)
    # Trim whitespace at line beginnings and endings
    result = "\n".join(line.strip() for line in result.split("\n"))
    return result


def get_line_indentation(line: str) -> str:
    """Extract the indentation (leading whitespace) from a line."""
    match = re.match(r"^(\s*)", line)
    return match.group(1) if match else ""


def preserve_indentation(old_text: str, new_text: str) -> str:
    """Preserve the indentation pattern from old_text in new_text.

    This function adapts the indentation in the new text to match the pattern
    established in the old text, maintaining relative indentation between lines.
    """
    # Special case for markdown lists: don't modify indentation if the new text has list markers
    if ("- " in new_text or "* " in new_text) and (
        "- " in old_text or "* " in old_text
    ):
        return new_text

    old_lines = old_text.split("\n")
    new_lines = new_text.split("\n")

    # Handle empty content
    if not old_lines or not new_lines:
        return new_text

    # Extract the base indentation from the first line of old text
    base_indent = (
        get_line_indentation(old_lines[0]) if old_lines and old_lines[0].strip() else ""
    )

    # Pre-calculate indentation maps for efficiency
    old_indents = {
        i: get_line_indentation(line)
        for i, line in enumerate(old_lines)
        if line.strip()
    }
    new_indents = {
        i: get_line_indentation(line)
        for i, line in enumerate(new_lines)
        if line.strip()
    }

    # Calculate first line indentation length for relative adjustments
    first_new_indent_len = len(new_indents.get(0, "")) if new_indents else 0

    # Process each line with the appropriate indentation
    result_lines = []
    for i, new_line in enumerate(new_lines):
        # Empty lines remain empty
        if not new_line.strip():
            result_lines.append("")
            continue

        # Get current indentation in new text
        new_indent = new_indents.get(i, "")

        # Determine target indentation based on context
        if i < len(old_lines) and i in old_indents:
            # Matching line in old text - use its indentation
            target_indent = old_indents[i]
        elif i == 0:
            # First line gets base indentation
            target_indent = base_indent
        elif first_new_indent_len > 0:
            # Calculate relative indentation for other lines
            curr_indent_len = len(new_indent)
            indent_diff = max(0, curr_indent_len - first_new_indent_len)

            # Default to base indent but look for better match from previous lines
            target_indent = base_indent

            # Find the closest previous line with appropriate indentation to use as template
            for prev_i in range(i - 1, -1, -1):
                if prev_i in old_indents and prev_i in new_indents:
                    prev_old = old_indents[prev_i]
                    prev_new = new_indents[prev_i]
                    if len(prev_new) <= curr_indent_len:
                        # Add spaces to match the relative indentation
                        relative_spaces = curr_indent_len - len(prev_new)
                        target_indent = prev_old + " " * relative_spaces
                        break
        else:
            # When first line has no indentation, use the new text's indentation
            target_indent = new_indent

        # Apply the calculated indentation
        result_lines.append(target_indent + new_line.lstrip())

    return "\n".join(result_lines)


def find_exact_match(content: str, pattern: str) -> MatchResult:
    """Find an exact string match in the content."""
    if pattern in content:
        lines_before = content[: content.find(pattern)].count("\n")
        line_count = pattern.count("\n") + 1
        return MatchResult(
            matched=True,
            line_index=lines_before,
            line_count=line_count,
            details="Exact match found",
        )
    return MatchResult(matched=False, details="No exact match found")


def create_unified_diff(original: str, modified: str, file_path: str) -> str:
    """Create a unified diff between original and modified content."""
    original_lines = original.splitlines(True)
    modified_lines = modified.splitlines(True)

    diff_lines = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm="",
    )

    return "".join(diff_lines)


def apply_edits(
    content: str, edits: List[EditOperation], options: EditOptions = None
) -> Tuple[str, List[Dict[str, Any]], bool]:
    """
    Apply a list of edit operations to the content.

    Args:
        content: The original file content
        edits: List of edit operations
        options: Formatting options

    Returns:
        Tuple of (modified content, list of match results, changes_made flag)
    """
    if options is None:
        options = EditOptions()

    # Normalize line endings
    normalized_content = normalize_line_endings(content)

    # Store match results for reporting
    match_results = []
    changes_made = False

    # Process each edit
    for i, edit in enumerate(edits):
        normalized_old = normalize_line_endings(edit.old_text)
        normalized_new = normalize_line_endings(edit.new_text)

        # Skip if the replacement text is identical to the old text
        if normalized_old == normalized_new:
            match_results.append(
                {
                    "edit_index": i,
                    "match_type": "skipped",
                    "details": "No change needed - text already matches desired state",
                }
            )
            continue

        # Check if the new_text is already in the content
        if (
            normalized_new in normalized_content
            and normalized_old not in normalized_content
        ):
            match_results.append(
                {
                    "edit_index": i,
                    "match_type": "skipped",
                    "details": "Edit already applied - content already in desired state",
                }
            )
            continue

        # Try exact match
        exact_match = find_exact_match(normalized_content, normalized_old)

        # Process exact match (if found)
        if exact_match.matched:
            # For exact matches, find position in content
            start_pos = normalized_content.find(normalized_old)
            end_pos = start_pos + len(normalized_old)

            # Apply indentation preservation if requested
            if options.preserve_indentation:
                normalized_new = preserve_indentation(normalized_old, normalized_new)

            # Apply the edit
            normalized_content = (
                normalized_content[:start_pos]
                + normalized_new
                + normalized_content[end_pos:]
            )
            changes_made = True

            match_results.append(
                {
                    "edit_index": i,
                    "match_type": "exact",
                    "line_index": exact_match.line_index,
                    "line_count": exact_match.line_count,
                }
            )
        else:
            match_results.append(
                {
                    "edit_index": i,
                    "match_type": "failed",
                    "details": "No exact match found",
                }
            )
            # Log the failed match
            logger.warning(f"Could not find exact match for edit {i}")

    return normalized_content, match_results, changes_made


def edit_file(
    file_path: str,
    edits: List[Dict[str, str]],
    dry_run: bool = False,
    options: Dict[str, Any] = None,
    project_dir: Path = None,
) -> Dict[str, Any]:
    """
    Make selective edits to a file.

    Features:
        - Line-based and multi-line content matching
        - Whitespace normalization with indentation preservation
        - Multiple simultaneous edits with correct positioning
        - Indentation style detection and preservation
        - Git-style diff output with context
        - Smart detection of already-applied edits

    Args:
        file_path: Path to the file to edit (relative to project directory)
        edits: List of edit operations with old_text and new_text
        dry_run: If True, only preview changes without applying them
        options: Optional formatting settings
            - preserve_indentation: Keep existing indentation (default: True)
            - normalize_whitespace: Normalize spaces (default: True)
        project_dir: Project directory path

    Returns:
        Dict with diff output and match information including success status
    """
    # Validate parameters
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file path: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    # If project_dir is provided, normalize the path
    if project_dir is not None:
        abs_path, rel_path = normalize_path(file_path, project_dir)
        file_path = str(abs_path)

    # Validate file path exists
    if not os.path.isfile(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read file content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error while reading {file_path}: {str(e)}")
        raise ValueError(
            f"File '{file_path}' contains invalid characters. Ensure it's a valid text file."
        ) from e
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise

    # Convert edits to EditOperation objects
    edit_operations = []
    for edit in edits:
        old_text = edit.get("old_text")
        new_text = edit.get("new_text")
        if old_text is None or new_text is None:
            logger.error(f"Invalid edit operation: {edit}")
            raise ValueError(
                "Edit operations must contain 'old_text' and 'new_text' fields."
            )
        edit_operations.append(EditOperation(old_text=old_text, new_text=new_text))

    # Set up options with defaults or provided values
    edit_options = EditOptions(
        preserve_indentation=(
            options.get("preserve_indentation", True) if options else True
        ),
        normalize_whitespace=(
            options.get("normalize_whitespace", True) if options else True
        ),
    )

    # Apply edits
    try:
        modified_content, match_results, changes_made = apply_edits(
            original_content, edit_operations, edit_options
        )

        # Check for actual failures and already applied edits
        failed_matches = [r for r in match_results if r.get("match_type") == "failed"]
        already_applied = [
            r
            for r in match_results
            if r.get("match_type") == "skipped"
            and "already applied" in r.get("details", "")
        ]

        # Handle common result cases
        result = {
            "match_results": match_results,
            "file_path": file_path,
            "dry_run": dry_run,
        }

        # Case 1: Failed matches
        if failed_matches:
            result.update(
                {
                    "success": False,
                    "error": "Failed to find exact match for one or more edits",
                }
            )
            return result

        # Case 2: No changes needed (already applied or identical content)
        if not changes_made or (already_applied and len(already_applied) == len(edits)):
            result.update(
                {
                    "success": True,
                    "diff": "",  # Empty diff indicates no changes
                    "message": "No changes needed - content already in desired state",
                }
            )
            return result

        # Case 3: Changes needed - create diff
        diff = create_unified_diff(original_content, modified_content, file_path)
        result.update({"diff": diff, "success": True})

        # Write changes if not in dry run mode
        if not dry_run and changes_made:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(modified_content)
            except UnicodeEncodeError as e:
                logger.error(
                    f"Unicode encode error while writing to {file_path}: {str(e)}"
                )
                result.update(
                    {
                        "success": False,
                        "error": "Content contains characters that cannot be encoded. Please check the encoding.",
                    }
                )
                return result
            except Exception as e:
                logger.error(f"Error writing to file {file_path}: {str(e)}")
                result.update({"success": False, "error": str(e)})
                return result

        return result

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Exception in edit_file: {error_msg}")

        # Provide error information with match results if available
        return {
            "success": False,
            "error": error_msg,
            "match_results": (
                match_results
                if "match_results" in locals() and match_results
                else [
                    {
                        "edit_index": 0,
                        "match_type": "failed",
                        "details": "Exception encountered: " + error_msg,
                    }
                ]
            ),
            "file_path": file_path,
        }
