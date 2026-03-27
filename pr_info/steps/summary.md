# Issue #73: Enforce .gitignore as Security Boundary for All File Tools

## Summary

Currently, `.gitignore` is only enforced in `list_directory()` via `filter_with_gitignore()`. All other file tools (`read_file`, `save_file`, `edit_file`, `append_file`, `delete_this_file`, `move_file`) can operate on gitignored paths if the LLM knows or guesses the path. This creates a false sense of sandboxing.

**Goal:** Make `.gitignore` a hard security boundary — the LLM cannot interact with gitignored files/folders through any tool.

## Architectural / Design Changes

### Before (current state)

```
server.py tool handlers → file_tools utilities → filesystem
                                                   ↑
                         list_directory() is the ONLY tool that filters via .gitignore
                         All other tools have NO gitignore awareness
```

### After (target state)

```
server.py tool handlers
    │
    ├── _check_not_gitignored(path)  ← NEW shared guard (policy enforcement)
    │       │
    │       └── calls is_path_gitignored()  ← NEW in directory_utils.py (check logic)
    │               │
    │               ├── calls is_path_in_git_dir()  ← NEW shared helper (DRY)
    │               └── calls read_gitignore_rules() (existing)
    │
    └── file_tools utilities → filesystem
```

### Design Decisions

1. **Separation of concerns preserved**: Check logic stays in `directory_utils.py` (tools layer, MCP-agnostic). Policy enforcement stays in `server.py` (protocol layer).

2. **DRY `.git/` exclusion**: New `is_path_in_git_dir()` helper replaces the inline check in `_discover_files()` and is reused by `is_path_gitignored()`.

3. **No caching**: `.gitignore` is parsed fresh each call via existing `read_gitignore_rules()`. The file is small; avoids stale-cache bugs.

4. **Root `.gitignore` only**: Matches current `list_directory()` behavior.

5. **Always enforced**: No toggle — this is a security boundary, not a convenience filter.

6. **Works on non-existent paths**: `save_file` to a new path matching `.gitignore` patterns (e.g., `debug.log` when `*.log` is ignored) is also blocked.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/file_tools/directory_utils.py` | Add `is_path_in_git_dir()`, `is_path_gitignored()`; refactor `_discover_files()` |
| `src/mcp_workspace/server.py` | Add `_check_not_gitignored()` guard; call it in 6 tool handlers |
| `tests/file_tools/test_directory_utils.py` | Tests for `is_path_in_git_dir()` and `is_path_gitignored()` |
| `tests/test_server.py` | Tests for gitignore enforcement in all affected tool handlers |

## Files NOT Modified

| File | Reason |
|------|--------|
| `src/mcp_workspace/file_tools/file_operations.py` | Enforcement is at server layer, not utility layer |
| `src/mcp_workspace/file_tools/path_utils.py` | No changes needed |
| `src/mcp_workspace/file_tools/__init__.py` | New functions are imported directly by server.py from directory_utils |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | `is_path_in_git_dir()` + DRY refactor of `_discover_files()` + tests | `Add is_path_in_git_dir helper and DRY-refactor _discover_files` |
| 2 | `is_path_gitignored()` + tests | `Add is_path_gitignored utility function` |
| 3 | `_check_not_gitignored()` guard in server.py + enforcement in all 6 tools + tests | `Enforce gitignore as security boundary in all file tools` |
