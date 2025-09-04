# Step 6: Implement Consistent Error Messages

## Objective
Standardize error messages across all file operations to provide clear, actionable feedback to the LLM and end users.

## Prerequisites
- Steps 1-5 completed
- Move functionality fully implemented and tested

## Implementation Tasks

### 1. Create Error Messages Module
Create `src/mcp_server_filesystem/file_tools/error_messages.py`:

```python
"""Standardized error messages for file operations."""


class ErrorMessages:
    """Consistent error message templates for file operations."""
    
    # Path validation errors
    PATH_NOT_STRING = "Path must be a non-empty string, got {type}"
    PATH_OUTSIDE_PROJECT = "Security error: Path '{path}' is outside the project directory"
    PATH_TRAVERSAL = "Security error: Path contains directory traversal (..)"
    PROJECT_DIR_NOT_SET = "Project directory has not been set"
    
    # File/Directory existence errors
    FILE_NOT_FOUND = "File '{path}' does not exist"
    FILE_ALREADY_EXISTS = "File '{path}' already exists"
    DIRECTORY_NOT_FOUND = "Directory '{path}' does not exist"
    PARENT_DIR_NOT_FOUND = "Parent directory '{path}' does not exist"
    
    # Type errors
    NOT_A_FILE = "Path '{path}' is not a file (might be a directory)"
    NOT_A_DIRECTORY = "Path '{path}' is not a directory"
    
    # Permission errors
    PERMISSION_DENIED = "Permission denied: Cannot {operation} '{path}'"
    
    # Move operation specific
    MOVE_SOURCE_NOT_FOUND = "Cannot move: Source '{source}' does not exist"
    MOVE_DEST_EXISTS = "Cannot move: Destination '{dest}' already exists. Delete it first or choose a different name"
    
    # Content errors
    INVALID_CONTENT_TYPE = "Content must be a string, got {type}"
    UNICODE_DECODE_ERROR = "File '{path}' contains invalid UTF-8 characters"
    UNICODE_ENCODE_ERROR = "Content contains characters that cannot be encoded to UTF-8"
    
    # Git operation messages (informational, not errors)
    GIT_FALLBACK = "Git operation failed, using filesystem instead: {reason}"
```

### 2. Update Move Function with Consistent Errors
Update `move_file` in `src/mcp_server_filesystem/file_tools/file_operations.py`:

```python
# Add import at top
from mcp_server_filesystem.file_tools.error_messages import ErrorMessages

def move_file(
    source_path: str,
    destination_path: str,
    project_dir: Path,
    create_parents: bool = True,
    use_git_if_available: bool = True
) -> Dict[str, Any]:
    """Move or rename a file or directory."""
    
    # Input validation with consistent messages
    if not source_path or not isinstance(source_path, str):
        raise ValueError(ErrorMessages.PATH_NOT_STRING.format(
            type=type(source_path).__name__
        ))
    
    if not destination_path or not isinstance(destination_path, str):
        raise ValueError(ErrorMessages.PATH_NOT_STRING.format(
            type=type(destination_path).__name__
        ))
    
    if project_dir is None:
        raise ValueError(ErrorMessages.PROJECT_DIR_NOT_SET)
    
    # Normalize paths (normalize_path will raise with consistent messages)
    src_abs, src_rel = normalize_path(source_path, project_dir)
    dest_abs, dest_rel = normalize_path(destination_path, project_dir)
    
    # Check if source exists
    if not src_abs.exists():
        raise FileNotFoundError(ErrorMessages.MOVE_SOURCE_NOT_FOUND.format(
            source=source_path
        ))
    
    # Check for destination conflicts
    if dest_abs.exists() and not is_case_only_rename:
        raise FileExistsError(ErrorMessages.MOVE_DEST_EXISTS.format(
            dest=destination_path
        ))
    
    # Rest of implementation...
```

### 3. Update Other File Operations
Apply consistent error messages to existing operations:

```python
# In read_file:
if not abs_path.exists():
    raise FileNotFoundError(ErrorMessages.FILE_NOT_FOUND.format(path=file_path))

if not abs_path.is_file():
    raise IsADirectoryError(ErrorMessages.NOT_A_FILE.format(path=file_path))

# In save_file:
if content is None:
    logger.warning("Content is None, treating as empty string")
    content = ""
elif not isinstance(content, str):
    raise ValueError(ErrorMessages.INVALID_CONTENT_TYPE.format(
        type=type(content).__name__
    ))

# In delete_file:
if not abs_path.exists():
    raise FileNotFoundError(ErrorMessages.FILE_NOT_FOUND.format(path=file_path))

if not abs_path.is_file():
    raise IsADirectoryError(ErrorMessages.NOT_A_FILE.format(path=file_path))
```

### 4. Update Server Error Handling
Update server.py to maintain consistency at the API level:

```python
# In server.py, update each tool's error handling:

@mcp.tool()
def move_file(source_path: str, destination_path: str) -> Dict[str, Any]:
    """Move or rename a file or directory."""
    
    # Consistent validation messages
    if not source_path or not isinstance(source_path, str):
        logger.error(f"Invalid source path parameter: {source_path}")
        raise ValueError(ErrorMessages.PATH_NOT_STRING.format(
            type=type(source_path).__name__
        ))
    
    if not destination_path or not isinstance(destination_path, str):
        logger.error(f"Invalid destination path parameter: {destination_path}")
        raise ValueError(ErrorMessages.PATH_NOT_STRING.format(
            type=type(destination_path).__name__
        ))
    
    if _project_dir is None:
        raise ValueError(ErrorMessages.PROJECT_DIR_NOT_SET)
    
    # Rest of implementation...
```

### 5. Create Tests for Error Messages
Create `tests/file_tools/test_error_messages.py`:

```python
"""Tests for consistent error messages."""
import pytest
from pathlib import Path

from mcp_server_filesystem.file_tools.error_messages import ErrorMessages
from mcp_server_filesystem.file_tools.file_operations import (
    move_file, read_file, save_file, delete_file
)


class TestErrorMessageConsistency:
    """Test that error messages are consistent across operations."""
    
    def test_path_not_string_error(self, project_dir):
        """Test consistent error for non-string paths."""
        # Test with None
        with pytest.raises(ValueError) as exc:
            move_file(None, "dest.txt", project_dir)
        assert "non-empty string" in str(exc.value)
        assert "NoneType" in str(exc.value)
        
        # Test with number
        with pytest.raises(ValueError) as exc:
            read_file(123, project_dir)
        assert "non-empty string" in str(exc.value)
        assert "int" in str(exc.value)
    
    def test_file_not_found_consistency(self, project_dir):
        """Test consistent file not found messages."""
        # Move operation
        with pytest.raises(FileNotFoundError) as exc:
            move_file("nonexistent.txt", "dest.txt", project_dir)
        assert "Cannot move: Source 'nonexistent.txt' does not exist" in str(exc.value)
        
        # Read operation
        with pytest.raises(FileNotFoundError) as exc:
            read_file("missing.txt", project_dir)
        assert "File 'missing.txt' does not exist" in str(exc.value)
        
        # Delete operation
        with pytest.raises(FileNotFoundError) as exc:
            delete_file("gone.txt", project_dir)
        assert "File 'gone.txt' does not exist" in str(exc.value)
    
    def test_file_exists_error_actionable(self, project_dir):
        """Test that file exists errors include actionable hints."""
        # Create source and destination
        source = project_dir / "source.txt"
        source.write_text("content")
        dest = project_dir / "existing.txt"
        dest.write_text("existing")
        
        with pytest.raises(FileExistsError) as exc:
            move_file("source.txt", "existing.txt", project_dir)
        
        error_msg = str(exc.value)
        assert "Cannot move" in error_msg
        assert "already exists" in error_msg
        assert "Delete it first or choose a different name" in error_msg
    
    def test_permission_error_includes_operation(self, project_dir, monkeypatch):
        """Test permission errors include the operation context."""
        import shutil
        
        # Create a file
        test_file = project_dir / "test.txt"
        test_file.write_text("content")
        
        # Mock shutil.move to raise PermissionError
        def mock_move(*args):
            raise PermissionError("Access denied")
        
        monkeypatch.setattr(shutil, 'move', mock_move)
        
        with pytest.raises(PermissionError) as exc:
            move_file("test.txt", "new.txt", project_dir, use_git_if_available=False)
        
        error_msg = str(exc.value)
        # Should include operation context
        assert "Permission denied" in error_msg or "Access denied" in error_msg
```

## Verification Commands

```bash
# Run error message tests
pytest tests/file_tools/test_error_messages.py -v

# Test error consistency across all operations
pytest tests/file_tools/ -v -k "error"

# Check that all error paths are tested
pytest tests/file_tools/ --cov=mcp_server_filesystem.file_tools --cov-report=term-missing
```

## Success Criteria
- [ ] Error messages module created with standardized templates
- [ ] All file operations use consistent error messages
- [ ] Error messages include actionable hints where appropriate
- [ ] Error messages specify the exact path/file that caused the issue
- [ ] Permission errors include operation context
- [ ] Type errors show the actual type received
- [ ] Tests verify error message consistency
- [ ] No regression in existing functionality

## Error Message Principles
1. **Be Specific**: Include the actual path/filename in the error
2. **Be Actionable**: Provide hints on how to fix the problem
3. **Be Consistent**: Use the same phrasing for similar errors
4. **Include Context**: Show what operation failed and why
5. **Show Types**: When type errors occur, show what was received

## Notes
- This step improves user experience and debugging
- Consistent errors make the LLM more effective at error recovery
- Actionable hints reduce back-and-forth iterations
- This is a refactoring step that doesn't change functionality
