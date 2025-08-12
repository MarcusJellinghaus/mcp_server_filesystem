import difflib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from .path_utils import normalize_path

logger = logging.getLogger(__name__)


def edit_file(
    file_path: str,
    edits: List[Dict[str, str]],
    dry_run: bool = False,
    options: Dict[str, Any] = None,
    project_dir: Path = None,
) -> Dict[str, Any]:
    """
    Make selective edits to a file with simplified, reliable processing.

    This simplified version focuses on reliability over advanced features:
    - Exact string matching only (no fuzzy matching)
    - Basic indentation preservation (preserve exactly as provided)
    - Clear error reporting
    - Single pass editing

    Args:
        file_path: Path to file (relative to project_dir if provided)
        edits: List of {'old_text': str, 'new_text': str} operations
        dry_run: If True, return diff without writing changes
        options: Optional settings (preserve_indentation: bool, default True)
        project_dir: Base directory for relative paths

    Returns:
        {
            'success': bool,
            'diff': str,  # unified diff or empty if no changes
            'message': str,  # human readable status (optional)
            'match_results': List[Dict],  # for compatibility
            'file_path': str,
            'dry_run': bool
        }
    """

    # Input validation
    if not file_path or not isinstance(file_path, str):
        return _error_result(f"Invalid file_path: {file_path}")

    if not isinstance(edits, list) or not edits:
        return _error_result("edits must be a non-empty list")

    # Resolve file path
    if project_dir:
        abs_path, rel_path = normalize_path(file_path, project_dir)
        file_path = str(abs_path)
    else:
        abs_path = Path(file_path)

    if not abs_path.exists():
        raise FileNotFoundError(f"File not found: {abs_path}")

    if not abs_path.is_file():
        raise ValueError(f"Not a file: {abs_path}")

    # Read file content
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except UnicodeDecodeError:
        return _error_result(f"File contains invalid UTF-8: {abs_path}", file_path)
    except Exception as e:
        return _error_result(f"Cannot read file: {e}", file_path)

    # Validate edit operations
    for i, edit in enumerate(edits):
        if not isinstance(edit, dict):
            return _error_result(
                f"Edit {i} must be a dict, got {type(edit)}", file_path
            )

        if "old_text" not in edit or "new_text" not in edit:
            return _error_result(
                f"Edit {i} missing required keys 'old_text' or 'new_text'", file_path
            )

        if not isinstance(edit["old_text"], str) or not isinstance(
            edit["new_text"], str
        ):
            return _error_result(f"Edit {i} values must be strings", file_path)

    # Extract options
    preserve_indentation = True
    if options and "preserve_indentation" in options:
        preserve_indentation = options["preserve_indentation"]

    # Apply edits sequentially
    current_content = original_content
    match_results = []
    edits_applied = 0
    edits_failed = 0

    for i, edit in enumerate(edits):
        old_text = edit["old_text"]
        new_text = edit["new_text"]

        # Skip if no change needed
        if old_text == new_text:
            match_results.append(
                {
                    "edit_index": i,
                    "match_type": "skipped",
                    "details": "No change needed - text already matches desired state",
                }
            )
            continue

        # Check if old_text exists in current content
        if old_text in current_content:
            # Apply indentation preservation if requested
            final_new_text = new_text
            if preserve_indentation:
                final_new_text = _preserve_basic_indentation(old_text, new_text)

            # Apply replacement (only first occurrence)
            current_content = current_content.replace(old_text, final_new_text, 1)
            match_results.append(
                {
                    "edit_index": i,
                    "match_type": "exact",
                    "line_index": original_content[: original_content.find(old_text)].count(
                        "\n"
                    ),
                    "line_count": old_text.count("\n") + 1,
                }
            )
            edits_applied += 1
        else:
            # Check if edit is already applied (new_text exists and old_text doesn't)
            if preserve_indentation:
                # Need to check both the original new_text and the indentation-preserved version
                final_new_text = _preserve_basic_indentation(old_text, new_text)
                edit_already_applied = (final_new_text in current_content) or (new_text in current_content)
            else:
                edit_already_applied = new_text in current_content
            
            if edit_already_applied:
                match_results.append(
                    {
                        "edit_index": i,
                        "match_type": "skipped",
                        "details": "Edit already applied - content already in desired state",
                    }
                )
            else:
                match_results.append(
                    {
                        "edit_index": i,
                        "match_type": "failed",
                        "details": f"Text not found: {_truncate(old_text)}",
                    }
                )
                edits_failed += 1

    # Determine success - success if no edits failed (even if no changes made due to already applied)
    success = edits_failed == 0
    changes_made = current_content != original_content

    # Generate diff
    diff = ""
    if changes_made:
        diff = _create_diff(original_content, current_content, str(abs_path))

    # Create result message
    message = None
    if edits_failed > 0:
        message = f"Failed to find exact match for {edits_failed} edit(s)"
    elif not changes_made:
        message = "No changes needed - content already in desired state"

    # Write changes if not dry run
    if not dry_run and changes_made and success:
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(current_content)
        except Exception as e:
            return _error_result(f"Cannot write file: {e}", file_path)

    result = {
        "success": success,
        "diff": diff,
        "match_results": match_results,
        "file_path": file_path,
        "dry_run": dry_run,
    }

    if message:
        result["message"] = message

    # Add error field when there are failures for test compatibility
    if not success and edits_failed > 0:
        result["error"] = f"Failed to find exact match for {edits_failed} edit(s)"

    return result


def _error_result(error_msg: str, file_path: str = "") -> Dict[str, Any]:
    """Helper to create error result in expected format"""
    logger.error(error_msg)
    return {
        "success": False,
        "error": error_msg,
        "diff": "",
        "match_results": [
            {"edit_index": 0, "match_type": "failed", "details": error_msg}
        ],
        "file_path": file_path,
        "dry_run": False,
    }


def _truncate(text: str, max_len: int = 50) -> str:
    """Truncate text for error messages"""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _create_diff(original: str, modified: str, filename: str) -> str:
    """Create unified diff between original and modified content"""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    return "".join(
        difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm="",
        )
    )


def _preserve_basic_indentation(old_text: str, new_text: str) -> str:
    """
    Simple indentation preservation: match leading whitespace of first line.

    Much simpler than the original complex version - just copies the leading
    whitespace from the first line of old_text to all lines of new_text.
    """
    old_lines = old_text.split("\n")
    new_lines = new_text.split("\n")

    if not old_lines or not new_lines:
        return new_text

    # Extract leading whitespace from first line of old_text
    first_old_line = old_lines[0]
    leading_whitespace = ""
    for char in first_old_line:
        if char in " \t":
            leading_whitespace += char
        else:
            break

    # Apply to all lines of new_text (except empty lines)
    enhanced_new_lines = []
    for i, line in enumerate(new_lines):
        if i == 0:
            # First line: replace its leading whitespace with old's leading whitespace
            enhanced_new_lines.append(leading_whitespace + line.lstrip())
        elif line.strip():  # Non-empty line
            # Other lines: preserve relative indentation but add base indentation
            enhanced_new_lines.append(leading_whitespace + line)
        else:
            # Empty lines stay empty
            enhanced_new_lines.append("")

    return "\n".join(enhanced_new_lines)


# Legacy compatibility functions (simplified versions)
def normalize_line_endings(text: str) -> str:
    """Convert all line endings to Unix style (\n)."""
    return text.replace("\r\n", "\n")


def create_unified_diff(original: str, modified: str, file_path: str) -> str:
    """Create a unified diff between original and modified content."""
    return _create_diff(original, modified, file_path)
