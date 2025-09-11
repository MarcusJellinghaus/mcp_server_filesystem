# Step 4: Implement Reference Directory Listing Tool

## Objective
Create the `list_reference_directory()` MCP tool to list files in reference projects.

## WHERE
- **File**: `src/mcp_server_filesystem/server.py`
- **Function**: `list_reference_directory(reference_name: str) -> List[str]`
- **Decorator**: `@mcp.tool()` and `@log_function_call`
- **Utility**: Reuse `list_files_util()` from existing imports

## WHAT
```python
@mcp.tool()
@log_function_call
def list_reference_directory(reference_name: str) -> List[str]:
    """List files and directories in a reference project directory.

    Args:
        reference_name: Name of the reference project to list

    Returns:
        A list of filenames in the reference project directory
    """
    pass
```

## HOW
- Use existing `@mcp.tool()` and `@log_function_call` decorators
- Validate `reference_name` parameter (non-empty string, exists in `_reference_projects`)
- Reuse existing `list_files_util(".", project_dir=ref_path, use_gitignore=True)`
- Follow same error handling pattern as `list_directory()`
- Log warnings for invalid reference names

## ALGORITHM
```
1. Validate reference_name is non-empty string
2. Check if reference_name exists in _reference_projects
3. IF not found: log warning, return helpful error message
4. Get reference project path from _reference_projects[reference_name]
5. Call list_files_util(".", project_dir=ref_path, use_gitignore=True)
6. Return file list
```

## DATA
**Input**: `reference_name: str` - name of reference project  
**Output**: `List[str]` - list of files/directories in reference project  
**Error**: Helpful message if reference project not found  
**Reuse**: Same gitignore filtering as main project

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Steps 1-3, implement Step 4: Create the list_reference_directory() MCP tool.

In src/mcp_server_filesystem/server.py, add the list_reference_directory() function that lists files in a reference project. Reuse the existing list_files_util() function with the reference project path.

Include validation for the reference_name parameter and return helpful error messages for non-existent projects (following design decision for runtime error handling). Follow the same patterns as the existing list_directory() function.
```
