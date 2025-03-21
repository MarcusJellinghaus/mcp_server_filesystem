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


def detect_indentation(text: str) -> Tuple[str, int]:
    """Detect the indentation style (spaces or tabs) and the count."""
    lines = text.split("\n")
    space_pattern = re.compile(r"^( +)[^ ]")
    tab_pattern = re.compile(r"^(\t+)[^\t]")

    spaces = []
    tabs = []

    for line in lines:
        if not line.strip():
            continue

        space_match = space_pattern.match(line)
        if space_match:
            spaces.append(len(space_match.group(1)))

        tab_match = tab_pattern.match(line)
        if tab_match:
            tabs.append(len(tab_match.group(1)))

    # Determine which is more common
    if len(spaces) > len(tabs):
        # Use the most common space count
        if spaces:
            most_common = max(set(spaces), key=spaces.count)
            return " " * most_common, most_common
        return "    ", 4  # Default 4 spaces
    elif len(tabs) > 0:
        return "\t", 1

    return "    ", 4  # Default to 4 spaces if no indentation detected


def get_line_indentation(line: str) -> str:
    """Extract the indentation from a line."""
    match = re.match(r"^(\s*)", line)
    return match.group(1) if match else ""


def preserve_simple_indentation(old_text: str, new_text: str) -> str:
    """
    A simplified approach to preserving indentation from old_text in new_text.
    Works line-by-line to maintain relative indentation patterns.
    """
    old_lines = old_text.split("\n")
    new_lines = new_text.split("\n")

    # Handle empty content
    if not old_lines or not new_lines:
        return new_text

    # Extract the base indentation from the first line of old text
    base_indent = get_line_indentation(old_lines[0]) if old_lines else ""

    # Determine indentation unit and size once
    indent_unit, indent_size = detect_indentation(old_text)

    # Build indentation map (line number -> indentation) from old text
    old_indents = {}
    for i, line in enumerate(old_lines):
        if line.strip():  # Skip empty lines
            old_indents[i] = get_line_indentation(line)

    # Process new lines with preserved indentation
    result_lines = []

    # Track relative nesting level (from the new text's perspective)
    current_nesting_level = 0
    prev_indent_len = 0

    for i, new_line in enumerate(new_lines):
        if not new_line.strip():  # Keep empty lines as-is
            result_lines.append("")
            continue

        new_indent = get_line_indentation(new_line)
        new_indent_len = len(new_indent)

        # First line always gets the base indentation from old text
        if i == 0:
            result_lines.append(base_indent + new_line.lstrip())
            prev_indent_len = new_indent_len
            continue

        # Determine how nesting changed from previous line
        if new_indent_len > prev_indent_len:
            # Increased indentation level
            current_nesting_level += 1
        elif new_indent_len < prev_indent_len:
            # Decreased indentation level - find closest previous level
            level_change = (prev_indent_len - new_indent_len) // max(len(indent_unit), 1) if indent_unit else 1
            current_nesting_level = max(0, current_nesting_level - level_change)

        prev_indent_len = new_indent_len

        # Determine target indentation
        if i < len(old_lines) and i in old_indents:
            # If we have a corresponding line in the original, use its indentation
            target_indent = old_indents[i]
        else:
            # Otherwise apply relative nesting to base indentation
            base_indent_len = len(base_indent)
            target_indent = base_indent + (indent_unit * indent_size * current_nesting_level)

            # Try to find a similar indentation level in the original text
            for old_i, old_indent in old_indents.items():
                if len(old_indent) == base_indent_len + (indent_size * current_nesting_level):
                    target_indent = old_indent
                    break

        # Apply the target indentation
        result_lines.append(target_indent + new_line.lstrip())

    return "\n".join(result_lines)


def preserve_indentation(old_text: str, new_text: str) -> str:
    """Preserve the indentation pattern from old_text in new_text using a simplified approach."""
    return preserve_simple_indentation(old_text, new_text)


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

    # Check if all edits have already been applied (optimization)
    all_edits_already_applied = True
    for edit in edits:
        normalized_old = normalize_line_endings(edit.old_text)
        normalized_new = normalize_line_endings(edit.new_text)

        if options.preserve_indentation:
            normalized_new = preserve_indentation(normalized_old, normalized_new)

        # If old text is present and would be replaced with something different,
        # then we need to make a change
        if normalized_old in normalized_content and normalized_new != normalized_old:
            all_edits_already_applied = False
            break

    # If all edits are already applied, return early
    if all_edits_already_applied and edits:
        return normalized_content, [], False

    # Store match results for reporting
    match_results = []
    changes_made = False

    # Process each edit
    for i, edit in enumerate(edits):
        normalized_old = normalize_line_endings(edit.old_text)
        normalized_new = normalize_line_endings(edit.new_text)

        # Try exact match
        exact_match = find_exact_match(normalized_content, normalized_old)

        # Process exact match (if found)
        if exact_match.matched:
            # For exact matches, find position in content
            start_pos = normalized_content.find(normalized_old)
            end_pos = start_pos + len(normalized_old)

            if options.preserve_indentation:
                normalized_new = preserve_indentation(normalized_old, normalized_new)

            # Skip if the replacement text is identical to what's already there
            if normalized_old == normalized_new:
                match_results.append({
                    "edit_index": i,
                    "match_type": "skipped",
                    "details": "No change needed - text already matches desired state"
                })
                continue

            normalized_content = (
                normalized_content[:start_pos]
                + normalized_new
                + normalized_content[end_pos:]
            )
            changes_made = True

            match_results.append({
                "edit_index": i,
                "match_type": "exact",
                "line_index": exact_match.line_index,
                "line_count": exact_match.line_count,
                })

        else:  # No exact match
            match_results.append({
                "edit_index": i,
                "match_type": "failed",
                "details": "No exact match found",
            })
            raise ValueError(f"Could not find exact match for edit {i}")

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
        - Optimization to detect already-applied edits
        - Support for both camelCase and snake_case parameter names

    Args:
        file_path: Path to the file to edit (relative to project directory)
        edits: List of edit operations with old_text/oldText and new_text/newText
        dry_run: If True, only preview changes without applying them
        options: Optional formatting settings
            - preserve_indentation/preserveIndentation: Keep existing indentation (default: True)
            - normalize_whitespace/normalizeWhitespace: Normalize spaces (default: True)
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
        # Normalize the path to be relative to the project directory
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

    # Convert edits to EditOperation objects - handle both camelCase and snake_case keys
    edit_operations = []
    for edit in edits:
        old_text = edit.get("old_text", edit.get("oldText"))
        new_text = edit.get("new_text", edit.get("newText"))
        if old_text is None or new_text is None:
            logger.error(f"Invalid edit operation: {edit}")
            raise ValueError("Edit operations must contain 'old_text' and 'new_text' fields.")
        edit_operations.append(EditOperation(old_text=old_text, new_text=new_text))

    # Set up options
    edit_options = EditOptions()
    if options:
        # Handle both snake_case and camelCase option keys
        if "preserve_indentation" in options:
            edit_options.preserve_indentation = options["preserve_indentation"]
        elif "preserveIndentation" in options:
            edit_options.preserve_indentation = options["preserveIndentation"]

        if "normalize_whitespace" in options:
            edit_options.normalize_whitespace = options["normalize_whitespace"]
        elif "normalizeWhitespace" in options:
            edit_options.normalize_whitespace = options["normalizeWhitespace"]

    # Apply edits
    try:
        modified_content, match_results, changes_made = apply_edits(
            original_content, edit_operations, edit_options
        )

        # Check if any changes were made
        if not changes_made and edits:
            # No changes needed - content already in desired state
            return {
                "success": True,
                "diff": "",  # Empty diff indicates no changes
                "match_results": match_results,
                "dry_run": dry_run,
                "file_path": file_path,
                "message": "No changes needed - content already in desired state"
            }

        # Create diff
        diff = create_unified_diff(original_content, modified_content, file_path)

        # Write changes if not in dry run mode
        if not dry_run and changes_made:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(modified_content)
            except UnicodeEncodeError as e:
                logger.error(
                    f"Unicode encode error while writing to {file_path}: {str(e)}"
                )
                raise ValueError(
                    f"Content contains characters that cannot be encoded. Please check the encoding."
                ) from e
            except Exception as e:
                logger.error(f"Error writing to file {file_path}: {str(e)}")
                raise

        return {
            "success": True,
            "diff": diff,
            "match_results": match_results,
            "dry_run": dry_run,
            "file_path": file_path,
        }
    except Exception as e:
        error_msg = str(e)

        return {
            "success": False,
            "error": error_msg,
            "match_results": match_results,
            "file_path": file_path,
        }
