# File Move/Rename Feature Implementation Summary

## Overview
Add file move/rename functionality to the MCP File System Server that intelligently preserves git history when possible.

## Problem Statement
The current MCP File System Server lacks the ability to:
1. Rename or move files and directories
2. Preserve git history when moving git-tracked files

## Solution
Implement a new `move_file` tool that:
- Automatically preserves git history when moving tracked files
- Handles all file and directory move/rename operations
- Works seamlessly within the project directory
- Provides simple success/failure feedback

## Technical Approach
- Use GitPython library for git operations (required dependency)
- Add new module for git operations (`git_operations.py`)
- Extend existing file operations with move functionality
- Expose new functionality through MCP server tool with simplified interface
- Maintain backwards compatibility and existing code patterns
- Leverage existing `@log_function_call` decorator for automatic logging and error handling
- All automatic behaviors (parent directory creation, git usage) happen transparently
- Simplify error messages at the server endpoint level for LLM clarity

## Dependencies
- GitPython (>=3.1.0) - required dependency for git operations
- Existing dependencies remain unchanged

## Implementation Steps
1. **Step 1**: Create git operations module with detection functions
2. **Step 2**: Implement basic move functionality with filesystem operations
3. **Step 3**: Integrate git support for tracked files
4. **Step 4**: Add server endpoint and MCP tool
5. **Step 5**: Handle edge cases and improve robustness

## Testing Strategy
- Follow Test-Driven Development (TDD) approach
- Write tests before implementation for each step
- Use mocking for git operations to avoid requiring actual git repositories in tests
- Test both success and failure scenarios

## Success Criteria
- Files can be moved/renamed within the project directory
- Git history preserved automatically when applicable
- Simple boolean return (true for success, exception for failure)
- Works within project directory only
- All existing tests continue to pass
- New functionality has >90% test coverage
- Error messages at server endpoint are simplified for LLM clarity

## Error Message Strategy
- **Internal functions** (in file_operations.py, git_operations.py):
  - Can use detailed error messages for debugging
  - Include paths, system details, git errors for logging
- **Server endpoint** (in server.py, exposed to LLM):
  - Catches and simplifies all error messages
  - "File not found" instead of path details
  - "Destination already exists" instead of filesystem specifics
  - "Permission denied" instead of system error details
  - "Invalid path" for security violations
  - "Move operation failed" for unexpected errors

## File Structure Changes
```
src/mcp_server_filesystem/file_tools/
├── __init__.py (updated)
├── git_operations.py (new)
├── file_operations.py (updated)
└── ...

tests/file_tools/
├── test_git_operations.py (new)
├── test_move_operations.py (new) - includes edge cases
├── test_move_git_integration.py (new)
└── ...
```

## API Design
```python
# Server endpoint (exposed to LLM)
@mcp.tool()
def move_file(
    source_path: str,
    destination_path: str
) -> bool

# Returns: True if successful, raises exception otherwise
# All implementation details (git vs filesystem) hidden from LLM
# Error messages are simplified for LLM consumption:
#   - "File not found" (no path details)
#   - "Destination already exists" (no filesystem specifics)
#   - "Permission denied" (no system details)
```

## Risk Mitigation
- GitPython as required dependency in pyproject.toml
- Automatic error handling via `@log_function_call` decorator
- No breaking changes to existing API
- Simple, predictable behavior with all logic hidden internally
