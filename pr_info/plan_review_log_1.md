# Plan Review Log — Issue #92

## Round 1 — 2026-04-19

**Findings**:
- (Critical) Finding 6: Type mismatch between Steps 4 and 5 — `main.py` returns `Dict[str, ReferenceProject]` in Step 4 but `server.py` still expects `Dict[str, Path]` until Step 5, causing test failures between commits
- (Critical) Finding 8: `@log_function_call` decorator is sync-only — creates sync wrapper that breaks async handlers. FastMCP checks `asyncio.iscoroutinefunction()` which returns False for sync wrappers
- (Improvement) Finding 4: Missing `test_clone_empty_target_path` test in Step 1
- (Improvement) Finding 7: Step 4 test assertions not explicit about Path→ReferenceProject change
- (Improvement) Finding 10: Step 5 doesn't explicitly state `ensure_available` should be mocked as async no-op in existing handler tests
- (Improvement) Finding 14: `clear_clone_failure_cache` missing from vulture whitelist in Step 7
- (Improvement) Finding 17: Error handling pattern unclear — `SystemExit` vs `ValueError` inconsistency in Step 4
- (Non-issue) Finding 19: `pytest-asyncio` already in `pyproject.toml`
- 13 nit-level findings skipped (acceptable as-is)

**Decisions**:
- Finding 6: Accept — move server.py type changes from Step 5 into Step 4
- Finding 8: Accept — remove `@log_function_call` from async handlers in Step 5
- Finding 4: Accept — add test case to Step 1
- Finding 7: Accept — add explicit note about assertion changes
- Finding 10: Accept — add explicit mocking instructions
- Finding 14: Accept — add to vulture whitelist
- Finding 17: Accept — use ValueError + sys.exit(1) pattern consistently
- All nits: Skip

**User decisions**: None needed — all fixes straightforward

**Changes**:
- `step_1.md`: Added `test_clone_empty_target_path` to TestCloneRepo
- `step_4.md`: Added server.py type migration (moved from Step 5), explicit test assertion note, clarified ValueError error handling
- `step_5.md`: Narrowed scope to async+ensure_available only, removed `@log_function_call` from async handlers, added mocking instructions
- `step_7.md`: Added `_.clear_clone_failure_cache` to vulture whitelist

**Status**: Committed (b00bba0)

## Round 2 — 2026-04-19

**Findings**:
- (Critical) Finding 1: `@log_function_call` applied to async `search_reference_files` in Step 6 — same sync-only decorator problem as Step 5
- (Critical) Findings 2+3: `main.py` imports `get_remote_url` from `git_operations` but `tach.toml` doesn't declare this dependency — `tach check` will fail
- (Improvement) Finding 5: Step 4 is the largest step — needs sizing warning
- (Nit) Finding 7: Redundant `(ValueError, Exception)` catch in Step 3 pseudocode
- 3 nits skipped (test name, usage string, mocking scope)

**Decisions**:
- Finding 1: Accept — remove `@log_function_call` from `search_reference_files` in Step 6
- Findings 2+3: Accept — create `detect_and_verify_url()` helper in `reference_projects.py` (Step 2), have `main.py` import only from `reference_projects` (Step 4)
- Finding 5: Accept — add sizing warning to Step 4
- Finding 7: Accept — simplify to `except Exception`

**User decisions**: None needed

**Changes**:
- `step_2.md`: Added `detect_and_verify_url()` function spec and 5 test cases
- `step_3.md`: Simplified exception catch from `(ValueError, Exception)` to `Exception`
- `step_4.md`: Replaced inline URL logic with `detect_and_verify_url()` call, removed `git_operations` imports from main.py, added sizing warning
- `step_6.md`: Removed `@log_function_call` from async `search_reference_files`

**Status**: Changes applied, pending commit
