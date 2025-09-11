# Step 3: Implement Reference Project Discovery Tool

## Objective
Create the `get_reference_projects()` MCP tool for LLM discovery of available reference projects.

## WHERE
- **File**: `src/mcp_server_filesystem/server.py`
- **Function**: `get_reference_projects() -> List[str]`
- **Decorator**: `@mcp.tool()` and `@log_function_call`

## WHAT
```python
@mcp.tool()
@log_function_call
def get_reference_projects() -> List[str]:
    """Get list of available reference project names.
    
    Returns:
        A list of reference project names that can be used with 
        list_reference_directory() and read_reference_file()
    """
    pass
```

## HOW
- Use existing `@mcp.tool()` and `@log_function_call` decorators
- Follow same pattern as other simple tools like `list_directory()`
- Access global `_reference_projects` variable
- Return sorted list for consistent ordering
- Add comprehensive docstring explaining usage

## ALGORITHM
```
1. Check if _reference_projects is initialized
2. Extract keys (project names) from _reference_projects dict
3. Sort names alphabetically for consistent output
4. Return sorted list of names
5. Log the operation (handled by decorator)
```

## DATA
**Input**: None  
**Output**: `List[str]` - sorted list of reference project names  
**Example**: `["docs", "examples", "utils"]`  
**Error**: Empty list `[]` if no reference projects configured

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Steps 1-2, implement Step 3: Create the get_reference_projects() MCP tool.

In src/mcp_server_filesystem/server.py, add the get_reference_projects() function using the @mcp.tool() and @log_function_call decorators. It should return a sorted list of available reference project names from the global _reference_projects variable.

Follow the existing patterns used by other tools like list_directory(). Include a comprehensive docstring that explains how this tool helps LLMs discover available reference projects.
```
