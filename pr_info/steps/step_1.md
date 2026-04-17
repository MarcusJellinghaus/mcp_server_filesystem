# Step 1: Promote git_operations to Top-Level Package

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. This is step 1 of 5 for issue #104.
>
> **Task:** Move `src/mcp_workspace/file_tools/git_operations/` to `src/mcp_workspace/git_operations/` (promote to top-level sibling of `file_tools/`). Move `tests/file_tools/git_operations/` to `tests/git_operations/`. Update ALL imports project-wide. Remove git re-exports from `file_tools/__init__.py`. All checks must pass.
>
> **Approach:** Use `move_module` MCP tool where possible. Then verify and fix any remaining import references manually. This is a pure move — no logic changes.

## WHERE

### Source files to move (12 files)

```
src/mcp_workspace/file_tools/git_operations/  →  src/mcp_workspace/git_operations/
  __init__.py
  branches.py
  branch_queries.py
  commits.py
  compact_diffs.py
  core.py
  diffs.py
  file_tracking.py
  parent_branch_detection.py
  remotes.py
  repository_status.py
  staging.py
  workflows.py
```

### Test files to move (13 files)

```
tests/file_tools/git_operations/  →  tests/git_operations/
  __init__.py
  conftest.py
  test_branches.py
  test_branch_queries.py
  test_commits.py
  test_compact_diffs.py
  test_compact_diffs_header_only.py
  test_compact_diffs_integration.py
  test_diffs.py
  test_edge_cases.py
  test_file_tracking.py
  test_parent_branch_detection.py
  test_remotes.py
  test_repository_status.py
  test_staging.py
```

### Files to modify

- `src/mcp_workspace/file_tools/__init__.py` — remove git re-exports and `__all__` entries
- `src/mcp_workspace/file_tools/file_operations.py` — update import path (line 12-16)
- `vulture_whitelist.py` — update comment referencing `git_operations` path if needed

## WHAT

No new functions. This is a pure move + import update.

### Import changes in source

| File | Old import | New import |
|------|-----------|------------|
| `file_tools/__init__.py` | `from mcp_workspace.file_tools.git_operations import git_move, is_file_tracked, is_git_repository` | **DELETE these 3 lines + remove from `__all__`** |
| `file_tools/file_operations.py` | `from mcp_workspace.file_tools.git_operations import git_move as git_move_impl` | `from mcp_workspace.git_operations import git_move as git_move_impl` |
| `file_tools/file_operations.py` | `from mcp_workspace.file_tools.git_operations import (is_file_tracked, is_git_repository,)` | `from mcp_workspace.git_operations import (is_file_tracked, is_git_repository,)` |
| `git_operations/__init__.py` | `from mcp_workspace.file_tools.git_operations.file_tracking import ...` | `from mcp_workspace.git_operations.file_tracking import ...` |
| `git_operations/__init__.py` | `from mcp_workspace.file_tools.git_operations.repository_status import ...` | `from mcp_workspace.git_operations.repository_status import ...` |

### Import changes in tests (all test files)

All `from mcp_workspace.file_tools.git_operations.X import ...` → `from mcp_workspace.git_operations.X import ...`

Affected test files (each has 1-3 import lines to update):
- `test_branches.py` — `branch_queries`, `branches`
- `test_branch_queries.py` ��� `branch_queries`
- `test_commits.py` — `commits`, `workflows`
- `test_compact_diffs.py` — `compact_diffs`
- `test_compact_diffs_header_only.py` — `compact_diffs`
- `test_compact_diffs_integration.py` — `branch_queries`, `compact_diffs`
- `test_diffs.py` ��� `branch_queries`, `branches`, `diffs`
- `test_edge_cases.py` — `git_operations` (top-level `__init__`)
- `test_file_tracking.py` — `file_tracking`, `workflows`
- `test_parent_branch_detection.py` — `parent_branch_detection`
- `test_remotes.py` — `remotes`
- `test_repository_status.py` — `repository_status`
- `test_staging.py` — `staging`

### Internal imports (inside git_operations modules)

These use relative imports (`.core`, `.repository_status`, etc.) — **no changes needed**. Relative imports survive the move.

## HOW

### Approach

1. Move the entire `file_tools/git_operations/` directory to `git_operations/` at the `mcp_workspace` level
2. Move the entire `tests/file_tools/git_operations/` directory to `tests/git_operations/`
3. Update `git_operations/__init__.py` — change absolute imports from `mcp_workspace.file_tools.git_operations.*` to `mcp_workspace.git_operations.*`
4. Update `file_tools/__init__.py` — remove the 3 git import lines and the 3 `__all__` entries (`is_git_repository`, `is_file_tracked`, `git_move`)
5. Update `file_operations.py` — change 2 import lines
6. Update all 13 test files — find/replace `mcp_workspace.file_tools.git_operations` → `mcp_workspace.git_operations`
7. Delete the now-empty `src/mcp_workspace/file_tools/git_operations/` directory
8. Delete the now-empty `tests/file_tools/git_operations/` directory

### Pseudocode

```
move_directory(src/mcp_workspace/file_tools/git_operations/, src/mcp_workspace/git_operations/)
move_directory(tests/file_tools/git_operations/, tests/git_operations/)
update_imports(git_operations/__init__.py: absolute paths)
remove_git_reexports(file_tools/__init__.py)
update_imports(file_operations.py)
find_replace_all_tests("mcp_workspace.file_tools.git_operations" → "mcp_workspace.git_operations")
```

## DATA

No new data structures. Existing `__all__` in `file_tools/__init__.py` shrinks from 12 to 9 entries.

## Verification

```
pylint, mypy, pytest (unit tests only — exclude integration markers)
grep for "file_tools.git_operations" in src/ and tests/ — must return nothing
```
