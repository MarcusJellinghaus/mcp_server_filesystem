# Step 3: Discovery MCP Tool (TDD)

## Objective
Write tests for and implement the `get_reference_projects()` MCP tool for LLM discovery of available reference projects.

## WHERE
- **Test File**: `tests/test_reference_projects.py` (add MCP tools test class)
- **Implementation File**: `src/mcp_server_filesystem/server.py`
- **Function**: `get_reference_projects() -> List[str]`
- **Decorators**: `@mcp.tool()` and `@log_function_call`

## WHAT

### Phase 1: Write Tests First (TDD Red)
```python
# tests/test_reference_projects.py
class TestReferenceProjectMCPTools:
    """Test MCP tools functionality."""
    
    def test_get_reference_projects_empty(self):
        """Test discovery tool returns empty list when no projects."""
        
    def test_get_reference_projects_sorted(self):
        """Test discovery tool returns sorted list of project names."""
        
    def test_get_reference_projects_logging(self):
        """Test INFO level logging for discovery operations."""
```

### Phase 2: Implement to Pass Tests (TDD Green)
```python
# src/mcp_server_filesystem/server.py
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
- Use existing `@mcp.tool()` and `@log_function_call` decorators (exact copy)
- Follow same pattern as other simple tools like `list_directory()`
- Access global `_reference_projects` variable
- Return sorted list for consistent ordering
- Add comprehensive docstring explaining usage
- Use INFO level logging for discovery operations

## ALGORITHM
```
1. Check if _reference_projects is initialized
2. Extract keys (project names) from _reference_projects dict
3. Sort names alphabetically for consistent output
4. Return sorted list of names
5. Log the operation at INFO level (handled by decorator)
```

## DATA
**Input**: None  
**Output**: `List[str]` - sorted list of reference project names  
**Example**: `["docs", "examples", "utils"]`  
**Error**: Empty list `[]` if no reference projects configured

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Steps 1-2, implement Step 3: Create the get_reference_projects() MCP tool.

In src/mcp_server_filesystem/server.py, add the get_reference_projects() function using the @mcp.tool() and @log_function_call decorators (exact copy from existing tools). It should return a sorted list of available reference project names from the global _reference_projects variable.

Follow the existing patterns used by other tools like list_directory() exactly. Include a comprehensive docstring that explains how this tool helps LLMs discover available reference projects. Use INFO level logging for discovery operations.
```
