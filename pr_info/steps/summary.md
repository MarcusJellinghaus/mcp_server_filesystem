# Summary: Unified Git MCP Tool (#113)

## Goal

Replace 4 separate git MCP tools (`git_log`, `git_diff`, `git_status`, `git_merge_base`) with a single unified `git` tool and add 7 new read-only commands (`fetch`, `show`, `branch`, `rev_parse`, `ls_tree`, `ls_files`, `ls_remote`).

## Architecture / Design Changes

### Before
```
server.py  ──→  read_operations.py  (4 functions: git_log, git_diff, git_status, git_merge_base)
               arg_validation.py    (4 allowlists: LOG, DIFF, STATUS, MERGE_BASE)
```
4 separate `@mcp.tool()` registrations in `server.py`, each delegating to its own function.

### After
```
server.py  ──→  read_operations.py  (unified git() dispatcher + existing functions + new commands)
               arg_validation.py    (11 allowlists + branch safety check)
```
1 single `@mcp.tool()` registration in `server.py` delegating to a unified `git()` dispatcher.

### Key Design Decisions

1. **Generic helper `_run_simple_command()`** — Commands that follow the validate→execute→truncate pattern (status, merge_base, fetch, rev_parse, ls_tree, ls_files, ls_remote) use a shared helper instead of 7 copy-paste functions.

2. **Dedicated functions kept for complex commands** — `git_log` (search filtering), `git_diff` (compact rendering + search), `git_show` (compact + colon detection), `git_branch` (read-only flag enforcement) have enough unique logic to warrant their own functions.

3. **Dispatcher is a simple dict + function** — The unified `git()` function maps command → handler, applies per-command `max_lines` defaults, generates soft warnings for unsupported params, and delegates. No classes or new modules.

4. **`max_lines` uses `Optional[int] = None`** — Allows distinguishing "caller didn't specify" (apply per-command default) from "caller explicitly set 100".

5. **Existing functions unchanged** — `git_log`, `git_diff`, `git_status`, `git_merge_base` internals are preserved. The dispatcher calls them. Existing unit tests for these functions remain valid.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/git_operations/arg_validation.py` | Add 7 new allowlists, `BRANCH_REQUIRED_READ_FLAGS`, register in `_ALLOWLISTS` |
| `src/mcp_workspace/git_operations/read_operations.py` | Add `_run_simple_command()`, `git_show()`, `git_branch()`, unified `git()` dispatcher |
| `src/mcp_workspace/server.py` | Replace 4 tool functions with 1 unified `git()` tool |
| `tests/git_operations/test_arg_validation.py` | Add tests for 7 new allowlists + branch safety |
| `tests/git_operations/test_read_operations.py` | Add tests for new commands + dispatcher |
| `tests/test_server.py` | Replace 4 tool tests with unified `git` tool tests |
| `vulture_whitelist.py` | Replace 4 entries with `_.git` |
| `.claude/CLAUDE.md` | Update tool mapping table |

## Files NOT Modified

- `read_operations.py` existing functions (`git_log`, `git_diff`, `git_status`, `git_merge_base`) — internals preserved
- `compact_diffs.py`, `output_filtering.py`, `core.py` — no changes needed
- `remotes.py` — `fetch` is a fresh implementation, no reuse
- Architecture configs (`.importlinter`, `tach.toml`) — no new modules

## Implementation Order

1. **Step 1**: New allowlists in `arg_validation.py` (fetch, show, branch, rev_parse, ls_tree, ls_files, ls_remote) + tests
2. **Step 2**: `_run_simple_command()` helper + `git_show()` + `git_branch()` in `read_operations.py` + tests
3. **Step 3**: Unified `git()` dispatcher in `read_operations.py` + tests
4. **Step 4**: Replace 4 server tools with unified `git` tool + update server tests + vulture whitelist
5. **Step 5**: Update `.claude/CLAUDE.md` tool mapping table
