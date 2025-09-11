# Step 5: Implement Reference File Reading Tool

## Objective
Create the `read_reference_file()` MCP tool to read files from reference projects.

## WHERE
- **File**: `src/mcp_server_filesystem/server.py`
- **Function**: `read_reference_file(reference_name: str, file_path: str) -> str`
- **Decorator**: `@mcp.tool()` and `@log_function_call`
- **Utility**: Reuse `read_file_util()` from existing imports

## WHAT
```python
@mcp.tool()
@log_function_call
def read_reference_file(reference_name: str, file_path: str) -> str:
    """Read the contents of a file from a reference project.

    Args:
        reference_name: Name of the reference project
        file_path: Path to the file to read (relative to reference project directory)

    Returns:
        The contents of the file as a string
    """
    pass
```

## HOW
- Use existing `@mcp.tool()` and `@log_function_call` decorators
- Validate both `reference_name` and `file_path` parameters
- Reuse existing `read_file_util(file_path, project_dir=ref_path)`
- Follow same error handling pattern as `read_file()` function
- Apply same security validation (path traversal prevention)

## ALGORITHM
```
1. Validate reference_name (non-empty, exists in _reference_projects)
2. Validate file_path (non-empty string, same as read_file())
3. IF reference not found: log warning, return helpful error message
4. Get reference project path from _reference_projects[reference_name]
5. Call read_file_util(file_path, project_dir=ref_path)
6. Return file contents
```

## DATA
**Input**: `reference_name: str`, `file_path: str` - project name and relative file path  
**Output**: `str` - file contents  
**Error**: Helpful messages for invalid reference name or file errors  
**Security**: Same path validation as main project (reuses existing utilities)

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Steps 1-4, implement Step 5: Create the read_reference_file() MCP tool.

In src/mcp_server_filesystem/server.py, add the read_reference_file() function that reads files from reference projects. Reuse the existing read_file_util() function with the reference project path.

Follow the same validation patterns as the existing read_file() function for file_path parameter. Include reference_name validation and helpful error messages for non-existent projects. Maintain the same security model by reusing existing utilities.
```
