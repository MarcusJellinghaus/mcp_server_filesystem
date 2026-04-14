# Issue #94: Modernize reinstall_local.bat to match mcp-coder pattern

## Summary

Rewrite `tools/reinstall_local.bat` to follow the established 6-step pattern used across sibling repos (mcp-coder-utils, mcp-tools-py), and add the missing `tools/read_github_deps.py` helper that reads GitHub dependency overrides from `pyproject.toml`.

## Architectural / Design Changes

### Before
- `reinstall_local.bat` uses `%ERRORLEVEL%` (unreliable inside `if` blocks)
- Requires venv to be pre-activated by the caller
- No GitHub dependency override step — sibling packages only come from PyPI
- No finalization step — GitHub overrides can shadow local editable install
- Venv activation doesn't persist to caller after script ends
- Step numbering is inconsistent (jumps from 3/6 to 4/6)

### After
- Uses `setlocal enabledelayedexpansion` + `!ERRORLEVEL!` for reliable error handling
- Auto-creates `.venv` if missing; deactivates any active venv at start
- Uses `--python` flag on all `uv pip` commands (no dependency on caller's venv state)
- New `read_github_deps.py` reads `[tool.mcp-coder.install-from-github]` from `pyproject.toml` and emits `uv pip install` commands
- Finalization step re-runs `uv pip install -e .` so local source takes precedence
- `endlocal & set` trick persists venv activation to caller's shell
- Clean 0-6 step numbering

### No changes to
- `pyproject.toml` — the `[tool.mcp-coder.install-from-github]` config already exists
- Any Python source code under `src/`
- Any existing tests

## Files to Create or Modify

| File | Action | Description |
|------|--------|-------------|
| `tools/read_github_deps.py` | **CREATE** | Copy verbatim from reference (`p_coder-utils`, formerly `p_mcp_utils`). Self-contained script that reads GitHub deps from `pyproject.toml` and prints `uv pip install` commands |
| `tests/test_read_github_deps.py` | **CREATE** | Tests for `read_github_deps.py`, written from scratch (no reference test exists) |
| `tools/reinstall_local.bat` | **MODIFY** | Full rewrite following the 6-step template pattern |

## Implementation Steps

| Step | Commit | Description |
|------|--------|-------------|
| 1 | `feat: add read_github_deps.py with tests` | Create `tools/read_github_deps.py` (verbatim copy) + `tests/test_read_github_deps.py` (written from scratch) |
| 2 | `feat: rewrite reinstall_local.bat to match modern pattern` | Rewrite `tools/reinstall_local.bat` following the 6-step template from `p_coder-utils`, adapted for mcp-workspace |

## Key Adaptation Points (mcp-workspace vs p_coder-utils reference)

| Aspect | p_coder-utils (reference) | mcp-workspace (target) |
|--------|---------------------|------------------------|
| Steps | 0-6 (7 steps) | 0-6 (7 steps) |
| Uninstall list | `mcp-coder-utils mcp-coder mcp-tools-py mcp-workspace` | `mcp-workspace mcp-coder-utils mcp-config-tool mcp-tools-py mcp-coder` |
| Import check | `mcp_coder_utils` | `mcp_workspace` |
| CLI check | none (no CLI entry point) | `mcp-workspace.exe` |
| Dev extras | `.[dev]` | `.[dev]` (same) |
| `read_github_deps.py` | Exists | Copy verbatim (self-contained) |
