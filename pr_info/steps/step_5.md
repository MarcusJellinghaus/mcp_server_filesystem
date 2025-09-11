# Step 5: File Reading MCP Tool (TDD)

## Objective
Write tests for and implement the `read_reference_file()` MCP tool to read files from reference projects.

## WHERE
- **Test File**: `tests/test_reference_projects.py` (extend MCP tools test class)
- **Implementation File**: `src/mcp_server_filesystem/server.py`
- **Function**: `read_reference_file(reference_name: str, file_path: str) -> str`
- **Decorators**: `@mcp.tool()` and `@log_function_call`
- **Utility**: Reuse `read_file_util()` from existing imports

## WHAT

### Phase 1: Write Tests First (TDD Red)
```python
# tests/test_reference_projects.py (extend TestReferenceProjectMCPTools)
def test_read_reference_file_success(self):
    """Test reading file from valid reference project."""
    
def test_read_reference_file_project_not_found(self):
    """Test error handling for non-existent reference project."""
    
def test_read_reference_file_file_not_found(self):
    """Test error handling for non-existent file."""
    
def test_read_reference_file_security(self):
    """Test path traversal prevention (reuse existing security)."""
    
def test_read_reference_file_logging(self):
    """Test DEBUG level logging for file operations."""
```

### Phase 2: Implement to Pass Tests (TDD Green)
```python
# src/mcp_server_filesystem/server.py
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

## HOW (TDD Process)

### Phase 1: Write Tests (Red)
- Extend `TestReferenceProjectMCPTools` class in `tests/test_reference_projects.py`
- Write 5 focused tests covering success, error cases, and security
- Follow exact patterns from existing `tests/test_server.py`
- Tests should initially fail (red state)

### Phase 2: Implement (Green)
- Use existing `@mcp.tool()` and `@log_function_call` decorators (exact copy)
- Validate both `reference_name` and `file_path` parameters using exact patterns from existing tools
- Reuse existing `read_file_util(file_path, project_dir=ref_path)`
- Follow same error handling pattern as `read_file()` function exactly
- Apply same security validation (path traversal prevention) - reuse existing utilities
- Use DEBUG level logging for file operations

### Phase 3: Refactor
- Clean up implementation while keeping tests green
- Ensure consistency with existing `server.py` patterns

## ALGORITHM
```
1. Validate reference_name using exact error message patterns from existing tools
2. Validate file_path using exact patterns from read_file() function
3. IF reference not found: return helpful error message (exact replication of existing patterns)
4. Get reference project path from _reference_projects[reference_name]
5. Log operation at DEBUG level with reference project context
6. Call read_file_util(file_path, project_dir=ref_path)
7. Return file contents
```

## DATA
**Input**: `reference_name: str`, `file_path: str` - project name and relative file path  
**Output**: `str` - file contents  
**Error**: Helpful messages for invalid reference name or file errors  
**Security**: Same path validation as main project (reuses existing utilities)

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Steps 1-4, implement Step 5 using TDD approach: File reading MCP tool.

Phase 1 - Write Tests First:
Extend TestReferenceProjectMCPTools class in tests/test_reference_projects.py. Write 5 focused tests covering: success case, reference project not found, file not found, security (path traversal), and DEBUG level logging. Follow exact patterns from tests/test_server.py. Tests should initially fail.

Phase 2 - Implement to Pass Tests:
Add read_reference_file() function to src/mcp_server_filesystem/server.py. Use exact decorator patterns, validate both parameters using exact patterns from read_file(), reuse read_file_util(), exact error message replication, same security model, DEBUG level logging.

Phase 3 - Refactor:
Clean up implementation while keeping tests green. Ensure consistency with existing server.py patterns.
```
