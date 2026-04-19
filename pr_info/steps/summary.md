# Issue #77: Add Read-Only Git Operations (log, status, diff, merge-base)

## Overview

Add four MCP tools for read-only git operations: `git_log`, `git_diff`, `git_status`, `git_merge_base`. These eliminate Bash permission prompts for pure-read git commands during automated workflows.

## Architecture & Design Changes

### New Files

| File | Layer | Purpose |
|------|-------|---------|
| `src/mcp_workspace/git_operations/arg_validation.py` | Tools (security boundary) | Per-command flag allowlists + `validate_args()` |
| `src/mcp_workspace/git_operations/output_filtering.py` | Tools (output processing) | Structure-aware search/filtering + truncation |
| `src/mcp_workspace/git_operations/read_operations.py` | Tools (git execution) | `git_log()`, `git_diff()`, `git_status()`, `git_merge_base()` |
| `tests/git_operations/test_arg_validation.py` | Tests | Unit tests for allowlist validation |
| `tests/git_operations/test_output_filtering.py` | Tests | Unit tests for filtering (synthetic string inputs) |
| `tests/git_operations/test_read_operations.py` | Tests | Integration tests with real git repos |

### Modified Files

| File | Change |
|------|--------|
| `src/mcp_workspace/server.py` | Add 4 thin MCP `@mcp.tool()` wrappers |
| `tach.toml` | Add `mcp_workspace.git_operations` to `server.py` depends_on |
| `vulture_whitelist.py` | Add `_.git_log`, `_.git_diff`, `_.git_status`, `_.git_merge_base` |
| `tests/test_server.py` | Add tests for the 4 new server tool wrappers |

### Layer Diagram (after change)

```
server.py (protocol) ──imports──▸ git_operations.read_operations (tools)
                                      │
                         ┌────────────┼────────────┐
                         ▼            ▼            ▼
                  arg_validation  output_filtering  compact_diffs
                                      │
                                      ▼
                              compact_diffs.parse_diff  (reused)
```

### Key Design Decisions

1. **Allowlist over blocklist** — unknown flags are blocked by default (prevents CVE-2025-68144 class vulnerabilities)
2. **`--no-ext-diff --no-textconv` hardcoded** on `git diff` and `git log` — defense-in-depth against external program execution
3. **`pathspec` is a separate parameter** — tool injects `--` internally to prevent flag/pathspec confusion
4. **Reuse `parse_diff()` from `compact_diffs.py`** for structure-aware diff filtering instead of writing a new parser
5. **Filter after compact** — compact diff needs full diff for cross-file move detection
6. **`_safe_repo_context()`** used for all git operations — prevents Windows handle leaks
7. **Raw text return** for all tools — no structured returns, works with any `args` combination

### Security Model

- All `args` validated against per-command allowlists before execution
- Non-`-` arguments (refs, SHAs) pass through — git validates them
- `--` rejected in `args` (injected internally when `pathspec` is provided)
- `--no-ext-diff --no-textconv` hardcoded to prevent external program execution
- Centralized in `arg_validation.py` — single file to audit

## Implementation Steps

| Step | File(s) | Description |
|------|---------|-------------|
| 1 | `arg_validation.py` + tests | Allowlists and validation function |
| 2 | `output_filtering.py` + tests | Structure-aware filtering and truncation |
| 3 | `read_operations.py` + tests | Core git execution functions |
| 4 | `server.py` + config + tests | MCP wrappers, tach.toml, vulture whitelist |
