# Summary: Move git_operations from mcp_coder into mcp_workspace

**Issue:** #98 — Move git_operations (part 2 of 5 cross-repo refactor)

## Goal

Replace the flat module `src/mcp_workspace/file_tools/git_operations.py` (3 functions, 134 lines) with `mcp_coder`'s full `utils/git_operations/` package (13 files). This moves git primitives to live alongside file primitives in mcp_workspace, where they belong architecturally.

## Architectural / Design Changes

### Before
```
src/mcp_workspace/file_tools/
├── git_operations.py          ← flat module, 3 functions (is_git_repository, is_file_tracked, git_move)
├── file_operations.py         ← imports from git_operations.py
├── __init__.py                ← re-exports 3 git functions
└── ...
```

### After
```
src/mcp_workspace/file_tools/
├── git_operations/            ← package (13 files from mcp_coder)
│   ├── __init__.py            ← trimmed re-export: is_git_repository, is_file_tracked, git_move
│   ├── core.py                ← _safe_repo_context (Windows handle safety)
│   ├── branches.py
│   ├── branch_queries.py
│   ├── commits.py             ← import fix: mcp_coder_utils.subprocess_runner
│   ├── compact_diffs.py
│   ├── diffs.py
│   ├── file_tracking.py       ← is_file_tracked, git_move
│   ├── parent_branch_detection.py
│   ├── remotes.py
│   ├── repository_status.py   ← is_git_repository
│   ├── staging.py             ← staging operations
│   └── workflows.py
├── file_operations.py         ← NO CHANGES (imports resolve via __init__.py)
├── __init__.py                ← NO CHANGES (imports resolve via package __init__.py)
└── ...
```

### Key design decisions
- **Trimmed re-export**: `git_operations/__init__.py` re-exports only 3 names needed by existing consumers. Not mcp_coder's full ~30-symbol `__all__`. YAGNI.
- **Submodule imports are the public contract** for downstream (issue ③): e.g., `from mcp_workspace.file_tools.git_operations.commits import commit_staged_files`.
- **Windows handle safety**: mcp_coder's `_safe_repo_context` properly cleans up GitPython processes/handles. Strictly better than current direct `Repo(...)` usage.
- **No MCP tool exposure**: No `@mcp.tool()` decorators — deferred to later issue.
- **Shared deps**: `mcp_coder_utils.subprocess_runner` and `mcp_coder_utils.log_utils` consumed directly (already a dependency).

### Config changes
- **`.importlinter`**: GitPython isolation ignore must cover submodules (`git_operations.core`, etc.)
- **`tach.toml`**: `file_tools` gains `mcp_coder_utils.subprocess_runner` dependency
- **`pyproject.toml`**: Register `git_integration` marker for `--strict-markers`

### Three deliberate behavior deltas (from issue)
1. `git_move` logs at DEBUG instead of INFO
2. `commits.py` import: `mcp_coder.utils.subprocess_runner` → `mcp_coder_utils.subprocess_runner`
3. All internal import paths: `mcp_coder.utils.git_operations.*` → `mcp_workspace.file_tools.git_operations.*`

## Files Created

| File | Description |
|------|-------------|
| `src/mcp_workspace/file_tools/git_operations/__init__.py` | Trimmed re-export (3 names) |
| `src/mcp_workspace/file_tools/git_operations/core.py` | `_safe_repo_context` |
| `src/mcp_workspace/file_tools/git_operations/branches.py` | Branch operations |
| `src/mcp_workspace/file_tools/git_operations/branch_queries.py` | Branch query operations |
| `src/mcp_workspace/file_tools/git_operations/commits.py` | Commit operations |
| `src/mcp_workspace/file_tools/git_operations/compact_diffs.py` | Compact diff formatting |
| `src/mcp_workspace/file_tools/git_operations/diffs.py` | Diff operations |
| `src/mcp_workspace/file_tools/git_operations/file_tracking.py` | `is_file_tracked`, `git_move` |
| `src/mcp_workspace/file_tools/git_operations/parent_branch_detection.py` | Parent branch detection |
| `src/mcp_workspace/file_tools/git_operations/remotes.py` | Remote operations |
| `src/mcp_workspace/file_tools/git_operations/repository_status.py` | Repository status queries |
| `src/mcp_workspace/file_tools/git_operations/staging.py` | Staging operations |
| `src/mcp_workspace/file_tools/git_operations/workflows.py` | Workflow operations |
| `tests/file_tools/git_operations/__init__.py` | Test package init |
| `tests/file_tools/git_operations/conftest.py` | Git test fixtures |
| `tests/file_tools/git_operations/test_*.py` | 12 `test_*.py` files from mcp_coder |
| `tests/file_tools/git_operations/test_edge_cases.py` | 5 consolidated edge-case tests |

## Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | Register `git_integration` marker |
| `.importlinter` | Update GitPython isolation for submodules |
| `tach.toml` | Add `mcp_coder_utils.subprocess_runner` dependency |

## Files Deleted

| File | Reason |
|------|--------|
| `src/mcp_workspace/file_tools/git_operations.py` | Replaced by package |
| `tests/file_tools/test_git_operations.py` | Duplicates removed; edge cases consolidated |
| `tests/integration_test_move.py` | Orphan manual script; not pytest-collected |

## Implementation Steps

1. **Config & cleanup** — Register marker, update architecture configs, delete orphan script
2. **Source package** — Copy 13 files, fix imports, delete flat module
3. **Tests** — Move 14 test files, consolidate edge cases, delete old test file
