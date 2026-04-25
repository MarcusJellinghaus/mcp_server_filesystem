# Plan Review Log — Issue #156 (GHE URL Support)

## Round 1 — 2026-04-25

**Findings**:
- Critical: Step 2 renames `get_github_repository_url` but doesn't update callers in `base_manager.py`/`pr_manager.py` — checks would fail after Step 2
- Step 3 creates throwaway intermediate code in `base_manager.py`/`pr_manager.py` that Steps 4-5 immediately replace
- `test_base_manager.py` touched in both Steps 3 and 4 (double-touch)
- `tach.toml` update in Step 1 is premature — no import from `utils` exists until Step 2
- Missing `tests/utils/__init__.py` creation
- `get_remote_url` docstring references old function name
- `test_pr_manager.py::test_repository_url_property` not addressed in Step 5
- Redundant `except (ValueError, Exception)` in Step 5 pseudo-code
- Unclear lifecycle for `tests/github_operations/test_repo_identifier.py`

**Decisions**:
- Accept (merge Steps 2+3): Eliminates broken imports, throwaway code, and double-touches — clearly the right fix
- Accept (tach.toml timing): Move to merged Step 2 where the import actually happens
- Accept (tests/utils/__init__.py): Add to Step 1
- Accept (docstring fix): Add to merged Step 2
- Accept (test_repository_url_property): Add to new Step 4
- Accept (exception handling): Fix in new Step 4
- Skip (test_repo_identifier lifecycle): Addressed as part of merged Step 2

**User decisions**: None needed — all findings were straightforward improvements.

**Changes**:
- Merged old Steps 2+3 into new Step 2 (atomic rename + deletion + caller updates)
- Renumbered old Step 4 → Step 3, old Step 5 → Step 4
- Deleted step_5.md
- Updated step_1.md (removed tach.toml, added tests/utils/__init__.py)
- Updated step_4.md (test_repository_url_property, exception fix)
- Updated summary.md and TASK_TRACKER.md for 4-step structure

**Status**: Committed (4a70d57)

## Round 2 — 2026-04-25

**Findings**:
- Critical: `src/mcp_workspace/github_operations/issues/cache.py` imports `RepoIdentifier` from `..github_utils` — will break when class is moved in Step 2
- Critical: `tests/github_operations/test_issue_cache.py` imports `RepoIdentifier` from `github_utils` — same breakage
- Critical: `tests/github_operations/test_ci_results_manager_foundation.py` asserts on `_repo_owner`/`_repo_name`/`_repo_full_name` — removed in Step 3
- Minor: Step 2 creates transitional code in `base_manager.py` that Step 3 removes (acceptable — intermediate state is functional)
- Note: Multiple test assertions on eager `Github()` creation need updating in Step 3 (already covered implicitly)

**Decisions**:
- Accept (cache.py): Add to Step 2 — straightforward import path update
- Accept (test_issue_cache.py): Add to Step 2 — straightforward import path update
- Accept (test_ci_results_manager_foundation.py): Add to Step 3 — straightforward assertion update
- Skip (transitional code): Acceptable trade-off — code is functional between steps
- Skip (eager Github assertions): Already covered by Step 3's test rewrite scope

**User decisions**: None needed.

**Changes**:
- Added `issues/cache.py` and `test_issue_cache.py` to Step 2
- Added `test_ci_results_manager_foundation.py` to Step 3
- Updated summary.md Files Modified table

**Status**: Committed (978d534)

## Round 3 — 2026-04-25

**Findings**:
- Exhaustive search across codebase for all affected symbols (parse_github_url, format_github_https_url, get_repo_full_name, get_github_repository_url, _parse_github_url, RepoIdentifier imports, _repo_owner/_repo_name/_repo_full_name, repository_url)
- Every file with matches is accounted for in the plan
- No coverage gaps found
- Step boundaries are clean — checks will pass after each step

**Decisions**: No changes needed.

**User decisions**: None.

**Changes**: None.

**Status**: No changes — review loop complete.

## Final Status

- **Rounds**: 3 (2 with changes, 1 validation pass)
- **Commits**: 2 (`4a70d57` — restructure 5→4 steps, `978d534` — add 3 missed files)
- **Plan status**: Ready for approval
- **Steps**: 4 (down from original 5)
- **Key changes made**:
  1. Merged original Steps 2+3 into atomic Step 2 (fixes import breakage between steps)
  2. Added `issues/cache.py`, `test_issue_cache.py` to Step 2 (missed RepoIdentifier imports)
  3. Added `test_ci_results_manager_foundation.py` to Step 3 (missed attribute assertions)
  4. Moved `tach.toml` update from Step 1 to Step 2 (correct timing)
  5. Added `tests/utils/__init__.py` to Step 1
  6. Fixed redundant exception handling in Step 4
