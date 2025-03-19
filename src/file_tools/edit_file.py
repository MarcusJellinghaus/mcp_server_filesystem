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
    partial_match: bool = True
    match_threshold: float = 0.8  # Confidence threshold for fuzzy matching


class MatchResult:
    """Stores information about a match attempt."""

    def __init__(
        self,
        matched: bool,
        confidence: float = 0.0,
        line_index: int = -1,
        line_count: int = 0,
        details: str = "",
    ):
        self.matched = matched
        self.confidence = confidence
        self.line_index = line_index
        self.line_count = line_count
        self.details = details

    def __repr__(self) -> str:
        return (
            f"MatchResult(matched={self.matched}, confidence={self.confidence:.2f}, "
            f"line_index={self.line_index}, line_count={self.line_count})"
        )


def normalize_text(text: str) -> str:
    """Normalize line endings and whitespace while preserving structure."""
    # Convert all line endings to Unix style
    text = text.replace("\r\n", "\n")
    # Collapse multiple spaces into one
    text = re.sub(r"[ \t]+", " ", text)
    # Trim whitespace at line beginnings and endings
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text


def get_indentation(line: str) -> str:
    """Extract the indentation from a line."""
    match = re.match(r"^(\s*)", line)
    return match.group(1) if match else ""


def preserve_indentation(old_text: str, new_text: str) -> str:
    """Preserve the indentation pattern from old_text in new_text with a robust approach."""
    old_lines = old_text.split("\n")
    new_lines = new_text.split("\n")

    # Handle empty content
    if not old_lines or not new_lines:
        return new_text

    # Get the base indentation and indentation pattern from old text
    indentation_levels = []
    for line in old_lines:
        if line.strip():  # Skip empty lines
            indent = get_indentation(line)
            if indent not in indentation_levels:
                indentation_levels.append(indent)

    # Sort indentation levels by length (shortest to longest)
    indentation_levels.sort(key=len)

    # Get the base indentation from the first line
    base_indent = get_indentation(old_lines[0]) if old_lines else ""

    # Process each line with appropriate indentation
    result_lines = []
    for i, new_line in enumerate(new_lines):
        # Skip empty lines
        if not new_line.strip():
            result_lines.append("")
            continue

        # For first line, use the base indentation from old text
        if i == 0:
            result_lines.append(base_indent + new_line.lstrip())
            continue

        # If we have a corresponding line in the old text, use its indentation
        if i < len(old_lines):
            old_indent = get_indentation(old_lines[i])
            result_lines.append(old_indent + new_line.lstrip())
            continue

        # Check if this is an appended block (like a new method in a class)
        if (
            i > 0
            and new_line.strip().startswith("def ")
            and len(get_indentation(new_line)) == 0
        ):
            # This is potentially a new method/function at the same level as existing ones
            # Find similar lines in old text
            method_indents = [
                get_indentation(line)
                for line in old_lines
                if line.strip().startswith("def ")
            ]
            if method_indents:
                result_lines.append(method_indents[0] + new_line.lstrip())
                continue

        # For new lines, analyze the indentation structure
        new_indent = get_indentation(new_line)
        prev_new_indent = get_indentation(new_lines[i - 1]) if i > 0 else ""
        prev_result_indent = (
            get_indentation(result_lines[-1]) if result_lines else base_indent
        )

        # Determine relative indentation level
        indent_diff = len(new_indent) - len(prev_new_indent)

        if indent_diff > 0:  # Increased indentation
            # Find closest matching indentation level in old text that's deeper than previous
            deeper_indents = [
                x for x in indentation_levels if len(x) > len(prev_result_indent)
            ]
            if deeper_indents:
                # Use the next deeper indentation level
                result_lines.append(deeper_indents[0] + new_line.lstrip())
            else:
                # Add standard indentation if no deeper level exists
                result_lines.append(prev_result_indent + "    " + new_line.lstrip())
        elif indent_diff < 0:  # Decreased indentation
            # Find closest matching indentation level in old text that's shallower than previous
            shallower_indents = [
                x for x in indentation_levels if len(x) < len(prev_result_indent)
            ]
            if shallower_indents:
                # Use the closest shallower indentation level
                closest_indent = max(shallower_indents, key=len)
                result_lines.append(closest_indent + new_line.lstrip())
            else:
                # Fallback to base indentation
                result_lines.append(base_indent + new_line.lstrip())
        else:  # Same indentation level
            result_lines.append(prev_result_indent + new_line.lstrip())

    return "\n".join(result_lines)


def find_match(
    content: str, pattern: str, partial_match: bool = True, threshold: float = 0.8
) -> MatchResult:
    """Find a match for pattern in content, supporting both exact and fuzzy matching."""
    # First try exact match
    if pattern in content:
        lines_before = content[: content.find(pattern)].count("\n")
        line_count = pattern.count("\n") + 1
        return MatchResult(
            matched=True,
            confidence=1.0,
            line_index=lines_before,
            line_count=line_count,
            details="Exact match found",
        )

    # If partial matching is disabled or pattern is empty, return no match
    if not partial_match or not pattern.strip():
        return MatchResult(
            matched=False,
            confidence=0.0,
            details="No exact match found and partial matching disabled",
        )

    # Try fuzzy matching
    content_lines = content.split("\n")
    pattern_lines = pattern.split("\n")

    best_confidence = 0.0
    best_index = -1

    # Scan through content lines to find the best match
    for i in range(len(content_lines) - len(pattern_lines) + 1):
        confidences = []

        # Check each line in the pattern against corresponding content
        for j, pattern_line in enumerate(pattern_lines):
            if not pattern_line.strip():  # Skip empty lines
                continue

            if i + j < len(content_lines):
                content_line = content_lines[i + j]
                similarity = difflib.SequenceMatcher(
                    None, content_line, pattern_line
                ).ratio()
                confidences.append(similarity)

        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            if avg_confidence > best_confidence:
                best_confidence = avg_confidence
                best_index = i

    # Return match if confidence is high enough
    if best_confidence >= threshold and best_index >= 0:
        return MatchResult(
            matched=True,
            confidence=best_confidence,
            line_index=best_index,
            line_count=len(pattern_lines),
            details=f"Fuzzy match with confidence {best_confidence:.2f}",
        )

    return MatchResult(
        matched=False,
        confidence=best_confidence,
        details=f"Best fuzzy match had confidence {best_confidence:.2f}, below threshold {threshold}",
    )


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
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Apply a list of edit operations to the content.
    """
    if options is None:
        options = EditOptions()

    modified_content = content.replace("\r\n", "\n")  # Normalize line endings
    match_results = []

    # Process each edit
    for i, edit in enumerate(edits):
        # Normalize line endings for consistent matching
        normalized_old = edit.old_text.replace("\r\n", "\n")
        normalized_new = edit.new_text.replace("\r\n", "\n")

        # Find match
        match_result = find_match(
            modified_content,
            normalized_old,
            options.partial_match,
            options.match_threshold,
        )

        if not match_result.matched:
            # No match found
            match_results.append(
                {
                    "edit_index": i,
                    "match_type": "failed",
                    "confidence": match_result.confidence,
                    "details": match_result.details,
                }
            )
            raise ValueError(
                f"Could not find match for edit {i}: {match_result.details}"
            )

        # Apply the replacement based on match type
        if match_result.confidence == 1.0:
            # Exact match replacement
            start_pos = modified_content.find(normalized_old)
            end_pos = start_pos + len(normalized_old)

            # Preserve indentation if needed
            replace_with = normalized_new
            if options.preserve_indentation:
                # Special handling for markdown bullet points
                if normalized_old.count('\n- ') > 0 and normalized_new.count('\n  - ') > 0:
                    # This is a markdown bullet point indentation change
                    # Use direct replacement without messing with indentation
                    replace_with = normalized_new
                else:
                    replace_with = preserve_indentation(normalized_old, normalized_new)

            modified_content = (
                modified_content[:start_pos] + replace_with + modified_content[end_pos:]
            )

            match_results.append(
                {
                    "edit_index": i,
                    "match_type": "exact",
                    "confidence": 1.0,
                    "line_index": match_result.line_index,
                    "line_count": match_result.line_count,
                }
            )
        else:
            # Fuzzy match replacement
            content_lines = modified_content.split("\n")
            line_index = match_result.line_index
            line_count = match_result.line_count

            # Extract matched content
            matched_content = "\n".join(
                content_lines[line_index : line_index + line_count]
            )

            # Preserve indentation if needed
            replace_with = normalized_new
            if options.preserve_indentation:
                # Special handling for markdown bullet points with fuzzy matching too
                if matched_content.count('\n- ') > 0 and normalized_new.count('\n  - ') > 0:
                    # This is a markdown bullet point indentation change
                    # Use direct replacement without messing with indentation
                    replace_with = normalized_new
                else:
                    replace_with = preserve_indentation(matched_content, normalized_new)

            # Replace the matched lines
            content_lines[line_index : line_index + line_count] = replace_with.split(
                "\n"
            )
            modified_content = "\n".join(content_lines)

            match_results.append(
                {
                    "edit_index": i,
                    "match_type": "fuzzy",
                    "confidence": match_result.confidence,
                    "line_index": line_index,
                    "line_count": line_count,
                }
            )

    return modified_content, match_results


def edit_file(
    file_path: str,
    edits: List[Dict[str, str]],
    dry_run: bool = False,
    options: Dict[str, Any] = None,
    project_dir: Path = None,
) -> Dict[str, Any]:
    """
    Make selective edits to a file using pattern matching.
    """
    # Validate parameters
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file path: {file_path}")
        raise ValueError(f"File path must be a non-empty string, got {type(file_path)}")

    # Normalize the path if project_dir is provided
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
    except UnicodeDecodeError:
        logger.error(f"Unicode decode error while reading {file_path}")
        raise ValueError(
            f"File '{file_path}' contains invalid characters. Ensure it's a valid text file."
        )
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise

    # Convert edits to EditOperation objects
    edit_operations = [
        EditOperation(old_text=edit["old_text"], new_text=edit["new_text"])
        for edit in edits
    ]

    # Set up options
    edit_options = EditOptions()
    if options:
        for key, value in options.items():
            if hasattr(edit_options, key):
                setattr(edit_options, key, value)

    match_results = []

    # Special case: Check if edits have already been applied
    # (to avoid errors on subsequent identical edits)
    # Check if we're trying to apply the same edits to an already edited file
    all_edits_already_done = True
    for edit in edit_operations:
        # If the original pattern is not found AND the new text is found, the edit was already done
        if edit.old_text not in original_content and edit.new_text in original_content:
            # Pattern already replaced
            continue
        else:
            all_edits_already_done = False
            break

    if all_edits_already_done:
        return {
            "success": True,
            "diff": "",
            "match_results": [],
            "dry_run": dry_run,
            "file_path": file_path,
            "message": "No changes needed - content already in desired state",
        }

    # Check that all patterns can be found
    for i, edit in enumerate(edit_operations):
        old_match = find_match(
            original_content,
            edit.old_text,
            edit_options.partial_match,
            edit_options.match_threshold,
        )
        if not old_match.matched:
            error_msg = f"Could not find match for edit {i}: {old_match.details}"
            if old_match.confidence > 0:
                error_msg = f"confidence too low: {old_match.details}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "match_results": [
                    {
                        "edit_index": i,
                        "match_type": "failed",
                        "confidence": old_match.confidence,
                        "details": old_match.details,
                    }
                ],
                "file_path": file_path,
            }

    # Special case for markdown bullet point indentation
    # This bypasses the regular edit process for better handling of markdown formatting
    is_markdown_bullet_edit = any('\n- ' in edit.old_text and '\n  - ' in edit.new_text 
                                for edit in edit_operations)
    
    if is_markdown_bullet_edit and not dry_run:
        # Use direct string replacement for these types of edits
        modified_content = original_content
        for edit in edit_operations:
            if '\n- ' in edit.old_text and '\n  - ' in edit.new_text:
                modified_content = modified_content.replace(edit.old_text, edit.new_text)
        
        # Create diff and match results
        diff = create_unified_diff(original_content, modified_content, file_path)
        match_results = [
            {
                "edit_index": i,
                "match_type": "direct",
                "confidence": 1.0,
                "details": "Direct replacement for markdown bullet point indentation"
            } for i, _ in enumerate(edit_operations)
        ]
        
        # Write changes
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
            
        return {
            "success": True,
            "diff": diff,
            "match_results": match_results,
            "dry_run": dry_run,
            "file_path": file_path,
        }
    
    # Apply edits
    try:
        modified_content, match_results = apply_edits(
            original_content, edit_operations, edit_options
        )

        # No changes needed if content is identical
        if modified_content == original_content:
            return {
                "success": True,
                "diff": "",
                "match_results": match_results,
                "dry_run": dry_run,
                "file_path": file_path,
                "message": "No changes needed - content already matches",
            }

        # Create diff
        diff = create_unified_diff(original_content, modified_content, file_path)

        # Write changes if not in dry run mode
        if not dry_run:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(modified_content)
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
        logger.error(f"Error applying edits to {file_path}: {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "match_results": match_results,
            "file_path": file_path,
        }
