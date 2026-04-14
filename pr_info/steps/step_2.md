# Step 2: Rewrite reinstall_local.bat to match modern pattern

> **Context**: See [summary.md](summary.md) for full issue context (#94).

## Commit Message
```
feat: rewrite reinstall_local.bat to match modern pattern
```

## Overview
Full rewrite of `tools/reinstall_local.bat` following the established 0-6 step template from `p_mcp_utils`, adapted for mcp-workspace's package list and CLI entry point.

## Files

### MODIFY: `tools/reinstall_local.bat`

**Reference**: `p_mcp_utils` project `tools/reinstall_local.bat` — adapt by:
- Adjusting uninstall list to 5 packages (adds `mcp-config-tool` vs reference's 4)
- Adding CLI entry point check (`mcp-workspace.exe --help`) alongside import check in step 5
- Updating import check to `mcp_workspace`

**Structure — 7 sections (steps 0–6):**

```
@echo off
setlocal enabledelayedexpansion

[Step 0] Check Python environment
  - Resolve PROJECT_DIR, VENV_DIR, VENV_SCRIPTS
  - call deactivate 2>nul (silently deactivate any active venv)
  - Check uv is available (where uv)
  - Auto-create .venv if missing (uv venv .venv)

[Step 1] Uninstall existing packages
  - uv pip uninstall mcp-workspace mcp-coder-utils mcp-config-tool mcp-tools-py mcp-coder --python "!VENV_SCRIPTS!\python.exe" 2>nul

[Step 2] Install with dev extras
  - pushd "!PROJECT_DIR!"
  - uv pip install -e ".[dev]" --python "!VENV_SCRIPTS!\python.exe"
  - popd

[Step 3] GitHub dependency overrides
  - Dry-run validate: "!VENV_SCRIPTS!\python.exe" tools\read_github_deps.py > nul 2>&1
  - for /f loop: parse and execute each command with --python flag

[Step 4] Finalize editable install
  - pushd "!PROJECT_DIR!"
  - uv pip install -e . --python "!VENV_SCRIPTS!\python.exe"
  - popd

[Step 5] Verify import + CLI
  - "!VENV_SCRIPTS!\python.exe" -c "import mcp_workspace; print('OK')"
  - "!VENV_SCRIPTS!\mcp-workspace.exe" --help >nul 2>&1

[Step 6] Done + venv activation
  - endlocal & set "_REINSTALL_VENV=!VENV_DIR!"
  - Deactivate wrong venv if active
  - Activate correct venv (persists to caller)
```

**Key technical patterns** (all from reference):
- `setlocal enabledelayedexpansion` + `!ERRORLEVEL!` throughout
- `--python "!VENV_SCRIPTS!\python.exe"` on all `uv pip` commands
- `pushd`/`popd` around `uv pip install -e .` calls
- Dry-run validation of `read_github_deps.py` before `for /f` parsing
- `endlocal & set` on single line to escape setlocal scope

## Data — No Python data structures
This is a batch file rewrite. No Python return values or data structures.

## Verification
1. Run tests: `mcp__tools-py__run_pytest_check(extra_args=["-n", "auto"])`
2. Run pylint: `mcp__tools-py__run_pylint_check()`
3. Run mypy: `mcp__tools-py__run_mypy_check()`

(Tests and type checks are for the Python codebase — no unit tests for .bat files, but ensure no regressions.)

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.

Implement Step 2 of Issue #94: Rewrite tools/reinstall_local.bat.

1. Read the current tools/reinstall_local.bat
2. Read the reference from p_mcp_utils: tools/reinstall_local.bat (use read_reference_file)
3. Write the new tools/reinstall_local.bat following the 6-step structure in step_2.md:
   - Adapt the reference: adjust uninstall list to 5 packages, update import check to mcp_workspace, add mcp-workspace.exe CLI check
4. Run all three quality checks (pylint, pytest excluding integration markers, mypy)
5. Fix any issues until all checks pass
6. Commit with message: "feat: rewrite reinstall_local.bat to match modern pattern"
```
