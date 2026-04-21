# Summary: Expand git_operations package exports (#127)

## Goal

Expand `mcp_workspace/git_operations/__init__.py` to re-export all 19 missing symbols that mcp_coder's shim needs, and rename `_safe_repo_context` → `safe_repo_context` since it's consumed cross-repo (public API).

## Architectural / Design Changes

### Before
- `git_operations/__init__.py` exports 14 symbols — a subset of the package's public surface
- `_safe_repo_context` uses underscore-prefix convention (private), but is consumed cross-repo by mcp_coder's shim

### After
- `git_operations/__init__.py` exports all 33 symbols (14 existing + 19 new) needed by downstream consumers
- `safe_repo_context` drops the underscore prefix, making it an explicitly public API — consistent with its cross-repo usage
- **No new modules, no new logic, no new classes** — purely a re-export expansion + rename
- The package's dependency chain remains unchanged: `mcp_coder → mcp_workspace → mcp_coder_utils`

### Design Decisions
- The rename is a mechanical find-and-replace across 10 submodule files (import line + call sites)
- All 19 "missing" symbols already exist in submodules — only `__init__.py` wiring is needed
- No circular dependency risk — git_operations has zero imports from path_utils or other domains

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/git_operations/core.py` | Rename `_safe_repo_context` → `safe_repo_context` |
| `src/mcp_workspace/git_operations/branch_queries.py` | Update import + usages |
| `src/mcp_workspace/git_operations/branches.py` | Update import + usages |
| `src/mcp_workspace/git_operations/commits.py` | Update import + usages |
| `src/mcp_workspace/git_operations/diffs.py` | Update import + usages |
| `src/mcp_workspace/git_operations/file_tracking.py` | Update import + usages |
| `src/mcp_workspace/git_operations/parent_branch_detection.py` | Update import + usages |
| `src/mcp_workspace/git_operations/remotes.py` | Update import + usages |
| `src/mcp_workspace/git_operations/repository_status.py` | Update import + usages |
| `src/mcp_workspace/git_operations/staging.py` | Update import + usages |
| `src/mcp_workspace/git_operations/workflows.py` | Update import + usages |
| `src/mcp_workspace/git_operations/__init__.py` | Add 19 new re-exports to imports + `__all__` |
| `vulture_whitelist.py` | Add newly-exported symbols that are unused internally |

## Files Created

None.

## Implementation Steps

1. **Step 1** — Rename `_safe_repo_context` → `safe_repo_context` in `core.py` + all 10 submodule consumers
2. **Step 2** — Expand `__init__.py` with 19 new re-exports + update `__all__` + update vulture whitelist
