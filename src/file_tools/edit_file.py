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

    # Get the base indentation from the first line of old text
    base_indent = get_indentation(old_lines[0]) if old_lines and old_lines[0].strip() else ""

    # Create a map of indentation levels from the old text
    old_indentation_map = {}
    for i, line in enumerate(old_lines):
        if line.strip():  # Skip empty lines
            stripped_line = line.lstrip()
            indent = line[:-len(stripped_line)] if stripped_line else line
            old_indentation_map[i] = indent

    # Process each line with appropriate indentation
    result_lines = []
    
    # Apply indentation for the first line
    if new_lines and new_lines[0].strip():
        result_lines.append(base_indent + new_lines[0].lstrip())
    elif new_lines:
        result_lines.append(new_lines[0])  # Keep empty lines as is
    
    # Process remaining lines
    for i in range(1, len(new_lines)):
        new_line = new_lines[i]
        
        # Skip processing for empty lines
        if not new_line.strip():
            result_lines.append("")
            continue
            
        # Get new line indentation and content
        new_indent = get_indentation(new_line)
        new_content = new_line.lstrip()
        
        # If we have a direct line mapping, use its indentation
        if i < len(old_lines) and old_lines[i].strip():
            old_indent = get_indentation(old_lines[i])
            result_lines.append(old_indent + new_content)
            continue
            
        # Otherwise analyze relative indentation from previous lines
        prev_new_line = new_lines[i-1]
        prev_new_indent = get_indentation(prev_new_line) if prev_new_line.strip() else ""
        prev_result_line = result_lines[-1] if result_lines else ""
        prev_result_indent = get_indentation(prev_result_line) if prev_result_line.strip() else base_indent
        
        # Handle special case for bullet points in markdown
        if new_content.startswith("- ") or new_content.startswith("* "):
            # For lists, use consistent 2-space indentation pattern
            if prev_result_line.lstrip().startswith(("- ", "* ")):
                # Determine if this is a sub-item based on input indentation
                if len(new_indent) > len(prev_new_indent):
                    # This is a sub-item, indent by 2 spaces from parent
                    result_lines.append(prev_result_indent + "  " + new_content)
                else:
                    # Same level item
                    result_lines.append(prev_result_indent + new_content)
            else:
                # First list item after non-list content
                result_lines.append(prev_result_indent + new_content)
            continue
            
        # Analyze relative indentation
        if prev_new_line.strip() and new_line.strip():
            # Calculate indent difference relative to previous line
            indent_diff = len(new_indent) - len(prev_new_indent)
            
            if indent_diff > 0:  # Increased indentation
                # For Python code blocks, typically use 4-space increments
                if new_content.startswith(("def ", "if ", "for ", "while ", "class ", "with ", "try:", "except:")):
                    result_lines.append(prev_result_indent + "    " + new_content.lstrip())
                else:
                    # Add the same number of spaces as in the new content
                    result_lines.append(prev_result_indent + " " * indent_diff + new_content)
            elif indent_diff < 0:  # Decreased indentation
                # Find an appropriate previous indentation level
                found_indent = False
                
                # Look for a matching indentation pattern in old text
                for j in range(i-1, -1, -1):
                    if j in old_indentation_map and len(old_indentation_map[j]) <= len(prev_result_indent):
                        # Found an earlier line with appropriate indentation
                        if len(old_indentation_map[j]) == len(prev_result_indent) + indent_diff:
                            result_lines.append(old_indentation_map[j] + new_content)
                            found_indent = True
                            break
                
                if not found_indent:
                    # If no appropriate previous indentation is found
                    # Calculate by removing the right amount of spaces
                    target_indent_len = max(0, len(prev_result_indent) + indent_diff)  
                    result_lines.append(prev_result_indent[:target_indent_len] + new_content)
            else:  # Same indentation level
                result_lines.append(prev_result_indent + new_content)
        else:
            # Default handling for lines without clear indentation relationship
            result_lines.append(base_indent + new_content)
    
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
        
        # Special case for markdown lists - detect if this is a markdown list edit
        is_markdown_list_edit = "- " in normalized_new and normalized_new.count("\n  - ") > 0

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

            # Apply the appropriate indentation strategy
            if is_markdown_list_edit:
                # For markdown list edits, use the exact formatting from the edit
                replace_with = normalized_new
            elif options.preserve_indentation:
                # Use preserve_indentation to handle indentation correctly
                replace_with = preserve_indentation(normalized_old, normalized_new)
            else:
                replace_with = normalized_new

            # Update content with the replacement
            modified_content = modified_content[:start_pos] + replace_with + modified_content[end_pos:]

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
            
            # When dealing with extreme indentation, we need to preserve it
            if is_markdown_list_edit:
                # For markdown list edits, use the exact formatting from the edit
                content_lines[line_index : line_index + line_count] = normalized_new.split("\n")
            elif options.preserve_indentation:
                # Identify if this is extremely indented content
                has_extreme_indent = any(len(get_indentation(line)) > 20 for line in matched_content.split('\n'))
                
                if has_extreme_indent:
                    # For extremely indented content, preserve the original indentation exactly
                    # Get indentation of each line in the original content
                    original_indents = []
                    for j in range(line_count):
                        if j < len(content_lines) - line_index:
                            original_indents.append(get_indentation(content_lines[line_index + j]))
                        else:
                            # If no more lines, use the last known indentation
                            original_indents.append(original_indents[-1] if original_indents else "")
                    
                    # Split the new content by lines
                    new_lines = normalized_new.split('\n')
                    result_lines = []
                    
                    # Apply the original exact indentation to each line
                    for j in range(len(new_lines)):
                        # If we have corresponding indentation, use it
                        if j < len(original_indents):
                            result_lines.append(original_indents[j] + new_lines[j].lstrip())
                        else:
                            # Otherwise use the indentation from the last line
                            result_lines.append(original_indents[-1] + new_lines[j].lstrip())
                    
                    # Replace the matched lines with our new properly indented lines
                    content_lines[line_index : line_index + line_count] = result_lines
                else:
                    # For normal content, use standard preserve_indentation
                    replace_with = preserve_indentation(matched_content, normalized_new)
                    content_lines[line_index : line_index + line_count] = replace_with.split("\n")
            else:
                # When not preserving indentation, use direct replacement
                content_lines[line_index : line_index + line_count] = normalized_new.split("\n")
                
            # Update content with modified lines
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
