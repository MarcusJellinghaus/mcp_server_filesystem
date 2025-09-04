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
    # Validate inputs
    if not source_path or not isinstance(source_path, str):
        raise ValueError(f"Source path must be a non-empty string")
    
    if not destination_path or not isinstance(destination_path, str):
        raise ValueError(f"Destination path must be a non-empty string")
    
    if _project_dir is None:
        raise ValueError("Project directory has not been set")
    
    # Call the underlying function (all logic is handled internally)
    result = move_file_util(source_path, destination_path, project_dir=_project_dir)
    
    # Return simple boolean - the decorator handles exceptions
    return result.get("success", False)
```

### 2. Update pyproject.toml
Add GitPython to dependencies:

```toml
dependencies = [
    # ... existing dependencies ...
    "GitPython>=3.1.0",  # Required for git operations
]
```

### 3. Update README.md
Add documentation for the new tool:

```markdown
#### Move File
- Parameters: `source_path`, `destination_path` 
- Returns: `bool` (true for success)
- Creates parent directories as needed
- Works within project directory only
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
