# Summary: Move github_operations + Restructure Module Layout (#104)

## Overview

Move `mcp_coder`'s `utils/github_operations/` package into `mcp_workspace/github_operations/` as a pure Python-API move. Restructure the module layout by promoting `git_operations/` out of `file_tools/` and placing `github_operations/` as a sibling. Add supporting infrastructure files (`config.py`, `constants.py`, `utils/timezone_utils.py`).

Part 3 of a 5-issue cross-repo refactor. After this PR, `mcp_workspace` owns file ops, git ops, and GitHub API ops — all MCP-agnostic Python APIs.

## Architectural Changes

### Before

```
src/mcp_workspace/
  main.py                        ← entry
  server.py                      ← protocol
  __init__.py
  file_tools/                    ← ALL tools nested here
    __init__.py                  ← re-exports git functions
    directory_utils.py
    edit_file.py
    file_operations.py           ← imports git_operations
    path_utils.py
    search.py
    git_operations/              ← nested under file_tools
      __init__.py
      branches.py, branch_queries.py, commits.py, ...
```

### After

```
src/mcp_workspace/
  main.py                        ← entry
  server.py                      ← protocol
  config.py                      ← NEW: token/repo resolution (utilities layer)
  constants.py                   ← NEW: DUPLICATE_PROTECTION_SECONDS
  __init__.py
  file_tools/                    ← file ops ONLY (no git re-exports)
    __init__.py                  ← git re-exports REMOVED
    directory_utils.py
    edit_file.py
    file_operations.py           ← imports from mcp_workspace.git_operations
    path_utils.py
    search.py
  git_operations/                ← PROMOTED from file_tools/
    __init__.py
    branches.py, branch_queries.py, commits.py, ...
  github_operations/             ← NEW: moved from mcp_coder
    __init__.py
    base_manager.py
    github_utils.py
    pr_manager.py
    labels_manager.py
    ci_results_manager.py
    issues/
      __init__.py
      base.py, branch_manager.py, branch_naming.py, cache.py,
      comments_mixin.py, events_mixin.py, labels_mixin.py,
      manager.py, types.py
  utils/                         ← NEW: shared utilities
    __init__.py
    timezone_utils.py            ← copied from mcp_coder
```

### Layer Changes

| Layer | Before | After |
|-------|--------|-------|
| entry | `main` | `main` (unchanged) |
| protocol | `server` | `server` (unchanged) |
| tools | `file_tools` (includes git) | `file_tools`, `git_operations`, `github_operations` (peers) |
| utilities | `mcp_coder_utils` | `mcp_coder_utils`, `config`, `constants`, `utils` |

### Dependency Rules (After)

- `github_operations` → `git_operations` (explicit peer dependency)
- `file_tools` → `git_operations` (for `git_move`, `is_file_tracked`)
- `git_operations`, `github_operations`, `file_tools` → `mcp_coder_utils` (logging, subprocess)
- `github_operations` → `config`, `constants`, `utils` (infrastructure)
- Only `github_operations/*` may import `github` (PyGithub) or `requests`

### Import Remap (Key Changes)

| Old import | New import |
|-----------|------------|
| `mcp_workspace.file_tools.git_operations.*` | `mcp_workspace.git_operations.*` |
| `mcp_workspace.file_tools.{git_move,is_file_tracked,is_git_repository}` | `mcp_workspace.git_operations.{...}` |
| `mcp_coder.utils.github_operations.*` | `mcp_workspace.github_operations.*` |
| `mcp_coder.utils.user_config.get_config_values` | `mcp_workspace.config.get_github_token` |
| `mcp_coder.constants.DUPLICATE_PROTECTION_SECONDS` | `mcp_workspace.constants.DUPLICATE_PROTECTION_SECONDS` |
| `mcp_coder.utils.timezone_utils.*` | `mcp_workspace.utils.timezone_utils.*` |

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_workspace/config.py` | `get_github_token()`, `get_test_repo_url()` |
| `src/mcp_workspace/constants.py` | `DUPLICATE_PROTECTION_SECONDS` |
| `src/mcp_workspace/utils/__init__.py` | Package init |
| `src/mcp_workspace/utils/timezone_utils.py` | Timezone utility (copied from mcp_coder) |
| `src/mcp_workspace/git_operations/__init__.py` | Promoted package init |
| `src/mcp_workspace/git_operations/*.py` | All 11 source modules (moved from file_tools/) |
| `src/mcp_workspace/github_operations/__init__.py` | Package init |
| `src/mcp_workspace/github_operations/base_manager.py` | Base GitHub manager class |
| `src/mcp_workspace/github_operations/github_utils.py` | GitHub utility functions |
| `src/mcp_workspace/github_operations/pr_manager.py` | PR management |
| `src/mcp_workspace/github_operations/labels_manager.py` | Label management |
| `src/mcp_workspace/github_operations/ci_results_manager.py` | CI results management |
| `src/mcp_workspace/github_operations/issues/__init__.py` | Issues subpackage init |
| `src/mcp_workspace/github_operations/issues/*.py` | 9 issue module files |
| `tests/git_operations/__init__.py` | Test package init |
| `tests/git_operations/conftest.py` | Moved test fixtures |
| `tests/git_operations/test_*.py` | All 12 test files (moved from tests/file_tools/) |
| `tests/github_operations/__init__.py` | Test package init |
| `tests/github_operations/conftest.py` | Test fixtures |
| `tests/github_operations/issues/__init__.py` | Test subpackage init |
| `tests/github_operations/issues/test_*.py` | Issue test files |
| `tests/github_operations/test_*.py` | Root-level github_operations tests |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/file_tools/__init__.py` | Remove git re-exports |
| `src/mcp_workspace/file_tools/file_operations.py` | Update git_operations import path |
| `pyproject.toml` | Add PyGithub dep, `github_integration` marker, CI marker config |
| `.importlinter` | Update layered arch, add PyGithub + requests isolation |
| `tach.toml` | Register new modules, peer tool layer |
| `vulture_whitelist.py` | Update for new module paths |
| `docs/ARCHITECTURE.md` | Update diagram and layer table |
| `.github/workflows/ci.yml` | Split pytest into unit-tests + integration-tests |

## Files Deleted

| File | Reason |
|------|--------|
| `src/mcp_workspace/file_tools/git_operations/` (entire dir) | Promoted to top-level |
| `tests/file_tools/git_operations/` (entire dir) | Moved to `tests/git_operations/` |

## Implementation Steps

1. **Promote git_operations** — Move source + tests to top-level, update all imports
2. **Add infrastructure files** — `config.py`, `constants.py`, `utils/timezone_utils.py` with tests
3. **Move github_operations source** — Copy from mcp_coder, adjust imports, add PyGithub dep
4. **Move github_operations tests** — Copy from mcp_coder, adjust imports and fixtures
5. **Update architecture enforcement + CI** — `.importlinter`, `tach.toml`, CI split

## Constraints

- **No `mcp_coder` imports** in mcp_workspace source after completion (grep verified)
- **No `label_config.py`, `labels.json`, `labels_schema.md`** in mcp_workspace
- **`update_workflow_label` deleted** from `manager.py`; `transition_issue_label` preserved
- **Move, don't change** — only import adjustments, no logic changes
- **`BaseGitHubManager`** takes `github_token: str` param (config-source-agnostic)
- **File size** — all files under 750 lines
