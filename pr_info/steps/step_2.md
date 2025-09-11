# Step 2: Add Reference Project Storage to Server

## Objective
Add global storage for reference projects and initialization function in the server module.

## WHERE
- **File**: `src/mcp_server_filesystem/server.py`
- **Module-level**: Add `_reference_projects` global variable
- **Function**: `set_reference_projects(reference_projects: Dict[str, Path]) -> None`
- **Function**: `run_server(project_dir: Path, reference_projects: Dict[str, Path] = None) -> None`

## WHAT
```python
# New module-level storage
_reference_projects: Dict[str, Path] = {}

# New function
def set_reference_projects(reference_projects: Dict[str, Path]) -> None:
    """Set the reference projects for file operations."""
    pass

# Modified function signature
def run_server(project_dir: Path, reference_projects: Dict[str, Path] = None) -> None:
    """Run the MCP server with project directory and optional reference projects."""
    pass
```

## HOW
- Add global `_reference_projects` variable similar to existing `_project_dir`
- Follow same pattern as `set_project_dir()` for reference project initialization
- Update `run_server()` to accept optional reference projects parameter
- Add logging for reference project initialization using existing logger patterns

## ALGORITHM
```
1. Initialize global _reference_projects as empty dict
2. In set_reference_projects():
   - Store reference_projects globally
   - Log each reference project name and path
3. In run_server():
   - Call set_project_dir() (existing)
   - IF reference_projects provided: call set_reference_projects()
   - Call mcp.run() (existing)
```

## DATA
**Input**: `Dict[str, Path]` - mapping of project names to directory paths  
**Storage**: `_reference_projects: Dict[str, Path]` - global module variable  
**Logging**: Info level messages for each reference project configured

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Step 1, implement Step 2: Add reference project storage to server.

In src/mcp_server_filesystem/server.py, add global storage for reference projects following the same pattern as the existing _project_dir variable. Create set_reference_projects() function and update run_server() to accept reference projects.

Follow the existing logging patterns and maintain backward compatibility. The run_server() signature should have reference_projects as an optional parameter with default None.
```
