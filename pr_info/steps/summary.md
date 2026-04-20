# Summary: Move git/github checks to mcp-workspace (#114)

## Overview

Move 5 modules and their tests from mcp-coder into mcp-workspace, then expose 3 as MCP tools. This is a **1:1 code migration** — no logic changes, only import adjustments.

## Architecture Changes

### New packages

| Package | Purpose |
|---------|---------|
| `src/mcp_workspace/checks/` | Branch status checks, file size checks |
| `src/mcp_workspace/workflows/` | Task tracker markdown parsing |

### Modules added to existing packages

| Module | Package |
|--------|---------|
| `base_branch.py` | `src/mcp_workspace/git_operations/` (existing) |
| `ci_log_parser.py` | `src/mcp_workspace/github_operations/` (existing) |

### New MCP tools (in `server.py`)

| Tool | Function called | Parameters |
|------|----------------|------------|
| `check_branch_status` | `collect_branch_status()` → `report.format_for_llm()` | `max_log_lines: int = 300` |
| `check_file_size` | `check_file_sizes()` → `render_output(result, max_lines)` | `max_lines: int = 600` |
| `get_base_branch` | `detect_base_branch()` (with DI) → fallback to `"main"` if None | none |

### Layer placement

```
server.py  (protocol layer — calls new tools)
  ├── checks/branch_status  (checks layer — above github_ops, depends on git_ops, github_ops, workflows)
  ├── checks/file_sizes     (checks layer — depends on file_tools)
  ├── file_tools | github_operations | reference_projects  (tools layer)
  ├── git_operations/base_branch | workflows/task_tracker  (tools layer — base_branch uses DI for github_ops)
  └── github_operations/ci_log_parser  (tools layer — existing package)
```

import-linter layers (top = highest):
```
server > server_reference_tools > checks > file_tools|github_operations|reference_projects > git_operations|workflows > config|constants|utils
```

Key constraint: `checks` is above `github_operations` because `branch_status.py` imports from `github_operations`. `base_branch.py` uses dependency injection to avoid importing from `github_operations` (which would be an upward import from `git_operations`).

### Config file changes

- **`.importlinter`**: Add `mcp_workspace.checks` (own layer above `file_tools | github_operations`) and `mcp_workspace.workflows` (at `git_operations` layer)
- **`tach.toml`**: Add `mcp_workspace.checks` and `mcp_workspace.workflows` module entries with dependencies; update `mcp_workspace.server` to depend on `mcp_workspace.checks` and `mcp_workspace.git_operations`
- **`vulture_whitelist.py`**: Add `check_branch_status`, `check_file_size`, `get_base_branch`

## Files created

| File | Type |
|------|------|
| `src/mcp_workspace/checks/__init__.py` | Package init |
| `src/mcp_workspace/checks/branch_status.py` | Source |
| `src/mcp_workspace/checks/file_sizes.py` | Source |
| `src/mcp_workspace/workflows/__init__.py` | Package init |
| `src/mcp_workspace/workflows/task_tracker.py` | Source |
| `src/mcp_workspace/git_operations/base_branch.py` | Source |
| `src/mcp_workspace/github_operations/ci_log_parser.py` | Source |
| `tests/checks/__init__.py` | Test package init |
| `tests/checks/test_branch_status.py` | Test |
| `tests/checks/test_branch_status_pr_fields.py` | Test |
| `tests/checks/test_file_sizes.py` | Test |
| `tests/workflows/__init__.py` | Test package init |
| `tests/workflows/test_task_tracker.py` | Test |
| `tests/workflows/test_data/*.md` | 5 test fixture files |
| `tests/git_operations/test_base_branch.py` | Test |
| `tests/github_operations/test_ci_log_parser.py` | Test |

## Files modified

| File | Change |
|------|--------|
| `src/mcp_workspace/server.py` | Add 3 MCP tool wrappers + imports |
| `.importlinter` | Add checks, workflows to layers |
| `tach.toml` | Add checks, workflows modules; update server deps |
| `vulture_whitelist.py` | Add 3 tool handler names |

## Implementation steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | `task_tracker.py` — pure markdown parser, no dependencies | `feat: add task_tracker module to workflows` |
| 2 | `ci_log_parser.py` — GitHub Actions log parsing | `feat: add ci_log_parser to github_operations` |
| 3 | `base_branch.py` — base branch detection + `get_base_branch` MCP tool | `feat: add base_branch detection and MCP tool` |
| 4 | `file_sizes.py` — file size checking + `check_file_size` MCP tool | `feat: add file_sizes check and MCP tool` |
| 5 | `branch_status.py` — branch status checks + `check_branch_status` MCP tool | `feat: add branch_status check and MCP tool` |
| 6 | Config updates — `.importlinter`, `tach.toml`, `vulture_whitelist.py` | `chore: update architecture configs for new modules` |

Step order rationale: dependencies flow upward — `task_tracker` and `ci_log_parser` have no internal deps, `branch_status` depends on both, so they come first.
