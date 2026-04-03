# Issue #76: Add `search_files` Tool — Implementation Summary

## Goal

Add a unified `search_files` MCP tool that combines file finding (glob) and content searching (regex) in a single call. This eliminates the need for Bash tools (`grep`, `find`, `rg`) in MCP-only workflows.

## Architecture / Design Changes

### New Files
| File | Layer | Purpose |
|------|-------|---------|
| `src/mcp_workspace/file_tools/search.py` | Tools | Business logic for glob matching and regex content search |
| `tests/file_tools/test_search.py` | Tests | Unit tests for search functionality |

### Modified Files
| File | Change |
|------|--------|
| `src/mcp_workspace/file_tools/__init__.py` | Export `search_files` |
| `src/mcp_workspace/server.py` | Wire up `@mcp.tool()` for `search_files` |
| `vulture_whitelist.py` | Add `_.search_files` entry |

### No Changes Needed
- `.importlinter` — `search.py` is within `file_tools`, already covered by existing contracts
- `tach.toml` — `file_tools` module boundary already defined
- `pyproject.toml` — no new dependencies (stdlib only: `re`, `pathlib`)

### Layered Architecture (unchanged)

```
main.py → server.py → file_tools/search.py → directory_utils.py (list_files)
                                             → path_utils.py (normalize_path)
```

- `server.py` (protocol layer): validates `_project_dir`, delegates to business logic
- `search.py` (tools layer): uses existing `list_files()` for gitignore-filtered file discovery, applies glob + regex filtering, handles output limiting
- No new external dependencies — uses stdlib `re` + `pathlib`

### Key Design Decisions
- **Reuse `list_files()`** from `directory_utils.py` for file discovery (already handles gitignore filtering) — no need to rename `_discover_files`
- **Single tool** combining find + grep — fewer tools = simpler for LLMs
- **Dual output cap**: `max_results` + `max_result_lines`, whichever hits first
- **Binary files skipped silently** on `UnicodeDecodeError` — no latin-1 fallback
- **`fnmatch.fnmatch()`** for glob (stdlib, no dependencies) — used instead of `PurePath.match()` because `PurePath.match()` does not support recursive `**` patterns on Python 3.11
- **`re.compile()`** for regex validation upfront

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| [Step 1](step_1.md) | Create `search.py` with business logic + tests for file search (glob-only) mode |  `feat: add search_files glob-only file search mode` |
| [Step 2](step_2.md) | Add content search (regex) mode + combined mode + tests | `feat: add search_files content and combined search modes` |
| [Step 3](step_3.md) | Wire up MCP tool in `server.py`, export, vulture whitelist | `feat: wire up search_files as MCP tool` |
