# Step 4: Add Server Endpoint and MCP Tool

## Objective
Expose the move functionality as an MCP tool in the server, making it accessible to AI assistants.

## Prerequisites
- Steps 1-3 completed (git operations, basic move, git integration)
- Move functionality fully tested and working

## Implementation Tasks

### 1. Add Server Endpoint
Add to `src/mcp_server_filesystem/server.py`:

```python
# Add import at the top
from mcp_server_filesystem.file_tools import move_file as move_file_util

@mcp.tool()
@log_function_call  
def move_file(
    source_path: str,
    destination_path: str
) -> bool:
    """Move or rename a file or directory within the project.
    
    Args:
        source_path: Source file/directory path (relative to project)
        destination_path: Destination path (relative to project)
        
    Returns:
        True if successful
        
    Raises:
        ValueError: If inputs are invalid
        FileNotFoundError: If source doesn't exist
        FileExistsError: If destination already exists
    """
    # Validate inputs with simple error messages
    if not source_path or not isinstance(source_path, str):
        raise ValueError("Invalid source path")
    
    if not destination_path or not isinstance(destination_path, str):
        raise ValueError("Invalid destination path")
    
    if _project_dir is None:
        raise ValueError("Project directory not configured")
    
    try:
        # Call the underlying function (all logic is handled internally)
        result = move_file_util(source_path, destination_path, project_dir=_project_dir)
        
        # Return simple boolean
        return result.get("success", False)
        
    except FileNotFoundError:
        # Simplify error message for LLM
        raise FileNotFoundError("File not found")
    except FileExistsError:
        # Simplify error message for LLM
        raise FileExistsError("Destination already exists")
    except PermissionError:
        # Simplify error message for LLM
        raise PermissionError("Permission denied")
    except ValueError as e:
        # For security errors, simplify the message
        if "Security" in str(e) or "outside" in str(e).lower():
            raise ValueError("Invalid path")
        raise ValueError("Invalid operation")
    except Exception:
        # Catch any other errors and simplify
        raise Exception("Move operation failed")
```

### 2. Update pyproject.toml
Add GitPython to dependencies:

```toml
dependencies = [
    # ... existing dependencies ...
    "GitPython>=3.1.0",  # Required for git operations
]
```

### 3. Create Server Tests
Add tests for the server endpoint to verify simplified error messages:

```python
# Add to tests/test_server.py

def test_move_file_simplified_errors(server_instance):
    """Test that server endpoint returns simplified error messages."""
    
    # Test file not found
    with pytest.raises(FileNotFoundError) as exc:
        server_instance.move_file("nonexistent.txt", "dest.txt")
    assert str(exc.value) == "File not found"  # Simple message
    
    # Test destination exists
    # ... create files first ...
    with pytest.raises(FileExistsError) as exc:
        server_instance.move_file("source.txt", "existing.txt")
    assert str(exc.value) == "Destination already exists"  # Simple message
    
    # Test permission error simulation
    # ... set up permission scenario ...
    with pytest.raises(PermissionError) as exc:
        server_instance.move_file("readonly.txt", "dest.txt")
    assert str(exc.value) == "Permission denied"  # Simple message
```

### 4. Update README.md
Add documentation for the new tool:

```markdown
#### Move File
- Parameters: `source_path`, `destination_path` 
- Returns: `bool` (true for success)
- Creates parent directories as needed
- Works within project directory only
- Simple error messages for clarity
```

## Verification Commands

```bash
# Install the package with GitPython
pip install -e .

# Run server tests
pytest tests/test_server.py -v

# Test the server manually
python -m mcp_server_filesystem.main --project-dir . --log-level DEBUG
```

## Success Criteria
- [ ] Server endpoint validates inputs
- [ ] MCP tool registration works
- [ ] Tool appears in MCP tool list
- [ ] All existing tests pass

## Notes
- Simple interface with just two parameters
- All automatic behaviors happen transparently
- Error handling via `@log_function_call` decorator
