# Step 4: Final Verification and Cleanup

## Context

Read `pr_info/steps/summary.md` for the full picture. Steps 1-3 are complete — all
code and tests have been rewritten. This step verifies everything works together and
cleans up any loose ends.

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file. Steps 1-3 are complete.
> Run all quality checks (pylint, pytest, mypy). Verify `__init__.py` exports and
> vulture whitelist are correct. Fix any remaining issues. Commit as one unit.

## WHERE — Files to verify (not modify unless broken)

- `src/mcp_workspace/file_tools/__init__.py` — confirm `edit_file` re-export works
- `vulture_whitelist.py` — confirm `_.edit_file` entry is still valid

## WHAT — Quality checks to run

1. `mcp__tools-py__run_pylint_check` — no new warnings
2. `mcp__tools-py__run_pytest_check` with `-n auto` and integration exclusions — all tests pass
3. `mcp__tools-py__run_mypy_check` — no type errors

## WHAT — Verification checklist

- [ ] `edit_file` utility returns `str` (not `Dict`)
- [ ] `edit_file` server tool is `async def`
- [ ] `_file_locks` dict exists in `server.py`
- [ ] No references to `old_text`/`new_text` in production code
- [ ] No references to `dry_run` in `edit_file` code paths
- [ ] No references to `preserve_indentation` in production code
- [ ] No references to `_error_result` or `_preserve_basic_indentation`
- [ ] No references to `create_unified_diff` (the public alias)
- [ ] `_is_edit_already_applied` still importable for test_edit_already_applied_fix.py
- [ ] All 5 test files pass
- [ ] No unused imports in modified files

## Decisions

- If `__init__.py` or `vulture_whitelist.py` need changes, include them in this commit
- If a test file has a minor issue from steps 1-3, fix it here rather than going back
- This is a cleanup/verification step — no new features
