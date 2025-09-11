# Step 4: Directory Listing MCP Tool (TDD)

## Objective
Write tests for and implement the `list_reference_directory()` MCP tool to list files in reference projects.

## WHERE
- **Test File**: `tests/test_reference_projects.py` (extend MCP tools test class)
- **Implementation File**: `src/mcp_server_filesystem/server.py`
- **Function**: `list_reference_directory(reference_name: str) -> List[str]`
- **Decorators**: `@mcp.tool()` and `@log_function_call`
- **Utility**: Reuse `list_files_util()` from existing imports

## WHAT

### Phase 1: Write Tests First (TDD Red)
```python
# tests/test_reference_projects.py (extend TestReferenceProjectMCPTools)
def test_list_reference_directory_success(self):
    """Test listing files in valid reference project."""
    
def test_list_reference_directory_not_found(self):
    """Test error handling for non-existent reference project."""
    
def test_list_reference_directory_gitignore(self):
    """Test gitignore filtering is applied."""
    
def test_list_reference_directory_logging(self):
    """Test DEBUG level logging for file operations."""
```

### Phase 2: Implement to Pass Tests (TDD Green)
```python
# src/mcp_server_filesystem/server.py
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

## HOW (TDD Process)

### Phase 1: Write Tests (Red)
- Extend `TestReferenceProjectMCPTools` class in `tests/test_reference_projects.py`
- Write 4 focused tests covering success case, error handling, gitignore, and logging
- Follow exact patterns from existing `tests/test_server.py`
- Tests should initially fail (red state)

### Phase 2: Implement (Green)
- Use existing `@mcp.tool()` and `@log_function_call` decorators (exact copy)
- Validate `reference_name` parameter using exact patterns from existing tools
- Reuse existing `list_files_util(".", project_dir=ref_path, use_gitignore=True)`
- Follow same error handling pattern as `list_directory()` exactly
- Use DEBUG level logging for file operations with reference project context

### Phase 3: Refactor
- Clean up implementation while keeping tests green
- Ensure consistency with existing `server.py` patterns

## ALGORITHM
```
1. Validate reference_name using exact error message patterns from existing tools
2. Check if reference_name exists in _reference_projects
3. IF not found: return helpful error message (exact replication of existing patterns)
4. Get reference project path from _reference_projects[reference_name]
5. Log operation at DEBUG level with reference project context
6. Call list_files_util(".", project_dir=ref_path, use_gitignore=True)
7. Return file list
```

## DATA
**Input**: `reference_name: str` - name of reference project  
**Output**: `List[str]` - list of files/directories in reference project  
**Error**: Helpful message if reference project not found  
**Reuse**: Same gitignore filtering as main project (use_gitignore=True)

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Steps 1-3, implement Step 4 using TDD approach: Directory listing MCP tool.

Phase 1 - Write Tests First:
Extend TestReferenceProjectMCPTools class in tests/test_reference_projects.py. Write 4 focused tests covering: success case, error handling for non-existent projects, gitignore filtering, and DEBUG level logging. Follow exact patterns from tests/test_server.py. Tests should initially fail.

Phase 2 - Implement to Pass Tests:
Add list_reference_directory() function to src/mcp_server_filesystem/server.py. Use exact decorator patterns, reuse list_files_util() with use_gitignore=True, exact error message patterns from existing tools, DEBUG level logging. Follow list_directory() patterns exactly.

Phase 3 - Refactor:
Clean up implementation while keeping tests green. Ensure consistency with existing server.py patterns.
```
