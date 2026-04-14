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
| `tools/read_github_deps.py` | **CREATE** | Copy verbatim from reference (`p_tools`). Self-contained script that reads GitHub deps from `pyproject.toml` and prints `uv pip install` commands |
| `tests/test_read_github_deps.py` | **CREATE** | Tests for `read_github_deps.py`, adapted from reference (`p_tools`) |
| `tools/reinstall_local.bat` | **MODIFY** | Full rewrite following the 6-step template pattern |

## Implementation Steps

| Step | Commit | Description |
|------|--------|-------------|
| 1 | `feat: add read_github_deps.py with tests` | Create `tools/read_github_deps.py` (verbatim copy) + `tests/test_read_github_deps.py` (adapted from reference) |
| 2 | `feat: rewrite reinstall_local.bat to match modern pattern` | Rewrite `tools/reinstall_local.bat` following the 6-step template from `p_tools`, adapted for mcp-workspace |

## Key Adaptation Points (mcp-workspace vs p_tools reference)

| Aspect | p_tools (reference) | mcp-workspace (target) |
|--------|---------------------|------------------------|
| Steps | 0-7 (8 steps, includes LangChain/MLflow) | 0-6 (7 steps, no LangChain/MLflow) |
| Uninstall list | `mcp-coder mcp-tools-py mcp-config mcp-workspace` | `mcp-workspace mcp-coder-utils mcp-config-tool mcp-tools-py mcp-coder` |
| Import check | `mcp_tools_py` | `mcp_workspace` |
| CLI check | `mcp-tools-py.exe` | `mcp-workspace.exe` |
| Dev extras | `.[dev]` | `.[dev]` (same) |
| `read_github_deps.py` | Exists | Copy verbatim (self-contained) |
