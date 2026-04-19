# Issue #92: Reference Project — Repo URL, Verify Config, Lazy Auto-Clone, Search

## Overview

Enhance reference project configuration to support repo URLs, URL verification, lazy auto-cloning of missing projects on first access, and search capability.

## Architecture & Design Changes

### New Module

- **`src/mcp_workspace/reference_projects.py`** — orchestration layer between `server.py` and `git_operations/`. Contains `ReferenceProject` dataclass, URL normalization, URL verification, and lazy clone logic.

### Architectural Layer Placement

```
main.py          (entry)
server.py        (protocol)
reference_projects.py | file_tools/ | github_operations/   (tools)   ← NEW
git_operations/  (tools - lower)
config | constants | utils  (utilities)
```

`reference_projects.py` sits at the same layer as `file_tools` — importable by both `main.py` and `server.py`, can import from `git_operations/`.

### Data Model Change

**Before:** `Dict[str, Path]` — simple name→directory mapping.

**After:** `Dict[str, ReferenceProject]` — typed dataclass with `name`, `path`, and optional `url`.

### CLI Format Change (Breaking)

```
# Old:  name=/path/to/dir
# New:  name=proj,path=/path/to/dir,url=https://github.com/org/repo
```

All keys are named. `name` and `path` required; `url` optional.

### New Git Primitives

Two functions added to `git_operations/remotes.py`:
- `get_remote_url(path)` — returns raw origin URL from any git repo
- `clone_repo(url, path)` — full clone via GitPython

### Lazy Cloning

- Triggered on first access (`read_reference_file`, `list_reference_directory`, `search_reference_files`)
- Uses `asyncio.Lock` per project to prevent concurrent clones
- Failures cached until server restart (no retry)

### API Response Change

`get_reference_projects()` returns objects with `name` + `url` instead of plain name strings.

### New MCP Tool

`search_reference_files()` — glob + regex search within a reference project, delegates to existing `search_files` utility.

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_workspace/reference_projects.py` | ReferenceProject dataclass, normalize_git_url, verify_url_match, ensure_available |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/git_operations/remotes.py` | Add `get_remote_url()`, `clone_repo()` |
| `src/mcp_workspace/git_operations/__init__.py` | Export new functions |
| `src/mcp_workspace/main.py` | New KV CLI parser, return `Dict[str, ReferenceProject]`, URL verification at startup |
| `src/mcp_workspace/server.py` | `Dict[str, ReferenceProject]`, async handlers, `ensure_available()` calls, `search_reference_files()` tool, updated API response |
| `.mcp.json` | Migrate 4 reference projects to new KV format |
| `.importlinter` | Add `mcp_workspace.reference_projects` to tools layer |
| `tach.toml` | Add `reference_projects` module block |
| `vulture_whitelist.py` | Add `_.search_reference_files` |
| `tests/test_reference_projects.py` | Update ~30 tests for new data model + format, add new tests |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| [Step 1](step_1.md) | Git primitives: `get_remote_url()` and `clone_repo()` |  |
| [Step 2](step_2.md) | `reference_projects.py`: dataclass, URL normalizer, URL verifier |  |
| [Step 3](step_3.md) | `reference_projects.py`: `ensure_available()` with async locking and failure cache |  |
| [Step 4](step_4.md) | `main.py` + `server.py`: KV CLI parser, URL verification, data model migration |  |
| [Step 5](step_5.md) | `server.py`: async handlers + `ensure_available()` integration |  |
| [Step 6](step_6.md) | `server.py`: `search_reference_files()` MCP tool + API response update |  |
| [Step 7](step_7.md) | Config files: `.importlinter`, `tach.toml`, `vulture_whitelist.py`, `.mcp.json` |  |
