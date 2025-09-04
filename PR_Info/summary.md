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
- Automatically creates parent directories when needed
- Provides clear feedback about which method was used

## Technical Approach
- Use GitPython library for git operations (with graceful fallback if not installed)
- Add new module for git operations (`git_operations.py`)
- Extend existing file operations with move functionality
- Expose new functionality through MCP server tool
- Maintain backwards compatibility and existing code patterns
- **Leverage existing logging infrastructure (`log_utils.py` and `@log_function_call` decorator)**

## Dependencies
- GitPython (>=3.1.0) - optional dependency with graceful degradation
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
- Git history is preserved for tracked files
- Parent directories are created automatically when needed
- Clear feedback about operation method (git vs filesystem)
- **All operations logged using existing dual-logging system (standard + structured)**
- All existing tests continue to pass
- New functionality has >90% test coverage

## File Structure Changes
```
src/mcp_server_filesystem/file_tools/
├── __init__.py (updated)
├── git_operations.py (new)
├── file_operations.py (updated)
└── ...

tests/file_tools/
├── test_git_operations.py (new)
├── test_move_operations.py (new)
└── ...
```

## API Design
```python
# Server endpoint
@mcp.tool()
def move_file(
    source_path: str,
    destination_path: str,
    create_parents: bool = True,
    use_git: bool = True
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
- GitPython is optional - system works without it
- Extensive error handling and logging
- Fallback mechanisms for all git operations
- No breaking changes to existing API
