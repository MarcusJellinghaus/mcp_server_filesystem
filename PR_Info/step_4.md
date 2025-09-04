# Step 4: Add Server Endpoint and MCP Tool

## Objective
Expose the move functionality as an MCP tool in the server, making it accessible to AI assistants like Claude.

## Prerequisites
- Steps 1-3 completed (git operations, basic move, git integration)
- Move functionality fully tested and working

## Test-Driven Development Approach
Write tests for the server endpoint, then add the MCP tool registration.

## Implementation Tasks

### 1. Create Server Endpoint Tests
Create or update `tests/test_server.py` to include move_file tests:

```python
"""Tests for server move_file endpoint."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp_server_filesystem.server import move_file as server_move_file, set_project_dir


class TestServerMoveEndpoint:
    """Test the move_file server endpoint."""
    
    def test_move_file_endpoint_basic(self, tmp_path):
        """Test basic move operation through server endpoint."""
        # Set project directory
        set_project_dir(tmp_path)
        
        # Create test file
        source = tmp_path / "test.txt"
        source.write_text("test content")
        
        # Call server endpoint
        result = server_move_file(
            source_path="test.txt",
            destination_path="moved.txt"
        )
        
        # Verify result
        assert result["success"] is True
        assert result["source"] == "test.txt"
        assert result["destination"] == "moved.txt"
        
        # Verify file was moved
        assert not source.exists()
        assert (tmp_path / "moved.txt").exists()
    
    def test_move_file_endpoint_with_parameters(self, tmp_path):
        """Test move with explicit parameters."""
        set_project_dir(tmp_path)
        
        # Create test file
        source = tmp_path / "source.txt"
        source.write_text("content")
        
        # Mock git operations to verify parameters are passed
        with patch('mcp_server_filesystem.file_tools.file_operations.is_git_repository') as mock_is_repo:
            with patch('mcp_server_filesystem.file_tools.file_operations.is_file_tracked') as mock_is_tracked:
                mock_is_repo.return_value = True
                mock_is_tracked.return_value = True
                
                # Call with explicit parameters
                result = server_move_file(
                    source_path="source.txt",
                    destination_path="dest.txt",
                    create_parents=False,
                    use_git=False
                )
                
                # Verify git was not checked (use_git=False)
                mock_is_repo.assert_not_called()
                mock_is_tracked.assert_not_called()
                assert result["method"] == "filesystem"
    
    def test_move_file_endpoint_validation(self, tmp_path):
        """Test endpoint input validation."""
        set_project_dir(tmp_path)
        
        # Test empty source path
        with pytest.raises(ValueError) as exc:
            server_move_file("", "dest.txt")
        assert "non-empty string" in str(exc.value)
        
        # Test empty destination path
        with pytest.raises(ValueError) as exc:
            server_move_file("source.txt", "")
        assert "non-empty string" in str(exc.value)
        
        # Test None source
        with pytest.raises(ValueError) as exc:
            server_move_file(None, "dest.txt")
        assert "non-empty string" in str(exc.value)
    
    def test_move_file_endpoint_no_project_dir(self):
        """Test that move fails when project directory is not set."""
        # Reset project directory to None
        set_project_dir(None)
        
        with pytest.raises(ValueError) as exc:
            server_move_file("source.txt", "dest.txt")
        assert "Project directory has not been set" in str(exc.value)
    
    def test_move_file_endpoint_with_subdirectories(self, tmp_path):
        """Test moving files to subdirectories through endpoint."""
        set_project_dir(tmp_path)
        
        # Create source file
        source = tmp_path / "file.txt"
        source.write_text("data")
        
        # Move to new subdirectory
        result = server_move_file(
            source_path="file.txt",
            destination_path="subdir/nested/file.txt",
            create_parents=True
        )
        
        assert result["success"] is True
        assert (tmp_path / "subdir" / "nested" / "file.txt").exists()
    
    def test_move_file_endpoint_error_handling(self, tmp_path):
        """Test error handling in server endpoint."""
        set_project_dir(tmp_path)
        
        # Try to move non-existent file
        with pytest.raises(FileNotFoundError) as exc:
            server_move_file("nonexistent.txt", "dest.txt")
        assert "does not exist" in str(exc.value)
        
        # Create a file
        source = tmp_path / "source.txt"
        source.write_text("content")
        
        # Try to move to existing destination
        dest = tmp_path / "existing.txt"
        dest.write_text("existing")
        
        with pytest.raises(FileExistsError) as exc:
            server_move_file("source.txt", "existing.txt")
        assert "already exists" in str(exc.value)
```

### 2. Add Server Endpoint
Add to `src/mcp_server_filesystem/server.py`:

```python
# Add import at the top
from mcp_server_filesystem.file_tools import move_file as move_file_util

@mcp.tool()
@log_function_call  # Already imported in server.py from log_utils
def move_file(
    source_path: str,
    destination_path: str,
    create_parents: bool = True,
    use_git: bool = True
) -> Dict[str, Any]:
    """
    Move or rename a file or directory.
    
    Automatically uses git mv for git-tracked files to preserve history.
    Creates parent directories if they don't exist (when create_parents=True).
    Falls back to filesystem operations for untracked files or when git fails.
    
    Args:
        source_path: Path to the file/directory to move (relative to project directory)
        destination_path: New path for the file/directory (relative to project directory)
        create_parents: Whether to create parent directories if they don't exist (default: True)
        use_git: Whether to use git mv for tracked files (default: True)
        
    Returns:
        Dict with operation details:
            - success: bool indicating if the move succeeded
            - method: 'git' or 'filesystem' indicating which method was used
            - source: normalized source path
            - destination: normalized destination path
            - message: descriptive message about the operation
            
    Examples:
        # Simple rename in same directory
        move_file("old_name.txt", "new_name.txt")
        
        # Move to subdirectory
        move_file("file.txt", "subfolder/file.txt")
        
        # Move with explicit filesystem (no git)
        move_file("tracked.txt", "moved.txt", use_git=False)
        
        # Move without creating parents
        move_file("file.txt", "existing_dir/file.txt", create_parents=False)
    """
    # Validate inputs at server level
    if not source_path or not isinstance(source_path, str):
        logger.error(f"Invalid source path parameter: {source_path}")
        raise ValueError(f"Source path must be a non-empty string, got {type(source_path)}")
    
    if not destination_path or not isinstance(destination_path, str):
        logger.error(f"Invalid destination path parameter: {destination_path}")
        raise ValueError(f"Destination path must be a non-empty string, got {type(destination_path)}")
    
    if _project_dir is None:
        raise ValueError("Project directory has not been set")
    
    logger.info(f"Moving file: {source_path} -> {destination_path} (git={use_git}, create_parents={create_parents})")
    
    try:
        # Call the underlying move function
        result = move_file_util(
            source_path,
            destination_path,
            project_dir=_project_dir,
            create_parents=create_parents,
            use_git_if_available=use_git
        )
        
        logger.info(f"Move completed: {result['source']} -> {result['destination']} using {result['method']}")
        return result
        
    except Exception as e:
        logger.error(f"Error moving file {source_path} to {destination_path}: {str(e)}")
        raise
```

### 3. Update pyproject.toml
Ensure `pyproject.toml` includes GitPython as a required dependency:

```toml
[project]
# ... existing configuration ...

dependencies = [
    "pathspec>=0.12.1",
    "igittigitt>=2.1.5",
    "mcp>=1.3.0",
    "mcp[server]>=1.3.0",
    "mcp[cli]>=1.3.0",
    "structlog>=25.2.0",
    "python-json-logger>=3.3.0",
    "GitPython>=3.1.0",  # Required for git operations
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.5",
    "pytest-asyncio>=0.25.3",
    "pylint>=3.3.3",
    "black>=24.10.0",
    "isort>=5.13.2",
    "mcp-code-checker @ git+https://github.com/MarcusJellinghaus/mcp-code-checker.git",
]
# ... rest of configuration ...
```

### 4. Update README.md
Add documentation for the new tool in the README:

```markdown
#### Move File
Moves or renames files and directories, automatically using git when appropriate.

- Parameters:
  - `source_path` (string): Path to the file/directory to move
  - `destination_path` (string): New path for the file/directory
  - `create_parents` (boolean, optional): Create parent directories if needed (default: true)
  - `use_git` (boolean, optional): Use git mv for tracked files (default: true)
- Returns: Dict with success status, method used (git/filesystem), and paths
- Features:
  - Automatically detects and uses git for version-controlled files
  - Creates parent directories when moving to new locations
  - Falls back to filesystem operations when git is unavailable
  - Preserves git history for tracked files

**Examples:**
```python
# Rename a file
move_file("old_name.py", "new_name.py")

# Move to a new directory (creates dir if needed)
move_file("src/util.py", "src/helpers/util.py")

# Force filesystem move (no git)
move_file("tracked.txt", "moved.txt", use_git=False)
```

**Note:** GitPython is installed automatically as a required dependency.
```

## Verification Commands

```bash
# Install the package (GitPython will be installed automatically)
pip install -e .

# Run server tests
pytest tests/test_server.py::TestServerMoveEndpoint -v

# Run all tests to ensure nothing broke
pytest tests/ -v

# Test the server manually
python -m mcp_server_filesystem.main --project-dir . --log-level DEBUG

# In another terminal, test with MCP client or Claude Desktop
# The move_file tool should now be available
```

## Success Criteria
- [ ] Server endpoint properly validates inputs
- [ ] Parameters are correctly passed to underlying function
- [ ] Proper error handling and logging
- [ ] MCP tool registration works
- [ ] Tool appears in MCP tool list
- [ ] Documentation is clear and complete
- [ ] All existing server tests still pass
- [ ] Project directory validation works

## Notes
- The server endpoint adds an additional validation layer
- Logging helps with debugging when used through MCP
- Clear documentation helps AI assistants use the tool correctly
- GitPython remains optional - noted in documentation
