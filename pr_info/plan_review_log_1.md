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

**Status**: Changes applied, pending commit
