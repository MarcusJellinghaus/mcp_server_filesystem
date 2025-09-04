# File Move/Rename Feature Implementation Summary

## Overview
Add file move/rename functionality to the MCP File System Server that intelligently uses `git mv` for git-tracked files to preserve history, while falling back to standard filesystem operations for untracked files.

## Problem Statement
The current MCP File System Server lacks the ability to:
1. Rename or move files and directories
2. Automatically create parent directories when moving files to non-existent paths
3. Preserve git history when moving git-tracked files

## Solution
Implement a new `move_file` tool that:
- Detects if a file is under git control
- Uses `git mv` for tracked files to preserve history
- Falls back to filesystem operations for untracked files
- Automatically creates parent directories (no parameter needed)
- Provides clear feedback about which method was used

## Technical Approach
- Use GitPython library for git operations (required dependency)
- Add new module for git operations (`git_operations.py`)
- Extend existing file operations with move functionality
- Expose new functionality through MCP server tool with simplified interface
- Maintain backwards compatibility and existing code patterns
- **Leverage existing logging infrastructure (`log_utils.py` and `@log_function_call` decorator)**
- **Implement consistent error message patterns with actionable hints**
- **Raise clear errors if GitPython is not installed**

## Dependencies
- GitPython (>=3.1.0) - required dependency for git operations
- Existing dependencies remain unchanged

## Implementation Steps
1. **Step 1**: Create git operations module with detection functions
2. **Step 2**: Implement basic move functionality with filesystem operations
3. **Step 3**: Integrate git support for tracked files
4. **Step 4**: Add server endpoint and MCP tool
5. **Step 5**: Handle edge cases and improve robustness
6. **Step 6**: Implement consistent error messages across all operations

## Testing Strategy
- Follow Test-Driven Development (TDD) approach
- Write tests before implementation for each step
- Use mocking for git operations to avoid requiring actual git repositories in tests
- Test both success and failure scenarios

## Success Criteria
- Files can be moved/renamed within the project directory
- Git history is preserved for tracked files
- Parent directories are created automatically
- Clear feedback about operation method (git vs filesystem)
- **All operations logged using existing dual-logging system (standard + structured)**
- **Consistent, actionable error messages across all operations**
- All existing tests continue to pass
- New functionality has >90% test coverage

## File Structure Changes
```
src/mcp_server_filesystem/file_tools/
├── __init__.py (updated)
├── error_messages.py (new)
├── git_operations.py (new)
├── file_operations.py (updated)
└── ...

tests/file_tools/
├── test_error_messages.py (new)
├── test_git_operations.py (new)
├── test_move_operations.py (new)
├── test_move_edge_cases.py (new)
├── test_move_git_integration.py (new)
└── ...
```

## API Design
```python
# Server endpoint
@mcp.tool()
def move_file(
    source_path: str,
    destination_path: str
) -> Dict[str, Any]

# Response format
{
    "success": bool,
    "method": "git" | "filesystem",
    "source": str,
    "destination": str,
    "message": str
}
```

## Risk Mitigation
- Clear dependency requirements in documentation and pyproject.toml
- Extensive error handling and logging
- Clear error messages if GitPython is not installed
- No breaking changes to existing API
- Simple, predictable behavior without conditional code paths
