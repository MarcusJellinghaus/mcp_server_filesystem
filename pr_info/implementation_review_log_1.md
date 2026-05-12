# Implementation Review Log — Issue #199 (Run 1)

**Branch:** `199-check-branch-status-pr-reviews-section-emits-unhelpful-threads-api-error`
**Date started:** 2026-05-12
**Scope:** Surface underlying exception detail in `check_branch_status` PR Reviews `[unavailable]` lines.

## Round 1 — 2026-05-12

**Findings** (from engineer subagent running `/implementation_review`):
- Diff confirmed real (4 files: 2 source + 2 tests).
- F1: Defensive `isinstance(raw, str)` guard on `exc.data["message"]` before `re.sub` — speculative; PyGithub sets `message` to a string. Engineer noted this exact case was raised and waived during plan review (Round 3).
- F2: Em-dash literal hard-coded in two f-strings; no module constant. Cosmetic.
- F3: Test `test_github_exception_non_dict_data_omits_message_segment` could carry a one-line comment about relying on the `isinstance(exc.data, dict)` guard. Style only.
- F4–F7: Truncation expression, insertion order, empty-state guard, architecture compliance — all verified correct.
- F8: No debug code / prints / `__main__` blocks.
- Quality checks: pylint, mypy, pytest (`-n auto`) all green. CI on origin green.
- Overall: implementation matches the approved plan in `pr_info/steps/summary.md`.

**Decisions**:
- F1 — **skip**. Speculative per Software Engineering Principles ("If a change only matters when someone makes a future mistake, it's speculative — skip it"). Decision already made during plan review (Round 3 of `plan_review_log_1.md`).
- F2 — **skip**. Cosmetic; the em-dash is mandated by the issue spec, no realistic churn driver.
- F3 — **skip**. Test name already conveys intent; docstring would add no information.
- F4–F8 — **no action** (positive verifications, not findings).

**Changes**: none.

**Status**: no changes needed.

## Round 2 — 2026-05-12

**Trigger**: Supervisor-side `mcp__mcp-tools-py__run_lint_imports_check` (run after Round 1) reported `PyGithub Library Isolation BROKEN` — `mcp_workspace.checks.pr_feedback -> github (l.12)`. The new `_render_exception` helper imported `GithubException` for `isinstance` discrimination, breaching the contract that only `mcp_workspace.github_operations.*` may import the `github` package.

**Findings**:
- Architectural violation: presentation layer (`checks/pr_feedback.py`) imports `github` package.
- The plan in `pr_info/steps/summary.md` placed rendering in the formatter ("Rendering lives in the formatter, not in `pr_manager.py`"), conflicting with the import-linter contract.

**Decisions**:
- Escalated to user with three options (move renderer / whitelist in `.importlinter` / pre-render in `pr_manager.py`).
- User selected **Move renderer into `github_operations`** — honors both architectural contracts; only the exception-string portion moves, formatter still owns line layout.

**Changes** (engineer subagent):
- Created `src/mcp_workspace/github_operations/exception_renderer.py` with public function `render_exception_for_display(exc: Exception) -> str`. Owns `import re` and `from github.GithubException import GithubException`.
- Modified `src/mcp_workspace/checks/pr_feedback.py`: removed `re` + `GithubException` imports and `_render_exception` body; added `from mcp_workspace.github_operations.exception_renderer import render_exception_for_display`; updated call site in `format_pr_feedback`.
- Created `tests/github_operations/test_exception_renderer.py` with unit tests for the renderer (GithubException variants, generic exceptions, whitespace handling, truncation).
- Modified `tests/checks/test_branch_status_pr_feedback.py`: trimmed `TestUnavailableSection` to three end-to-end cases (one `GithubException`, one generic exception, multi-section insertion order). No duplication across files.

**Quality gates** (supervisor-verified):
- `run_format_code`: applied.
- `run_pylint_check`: pass.
- `run_mypy_check`: pass.
- `run_pytest_check -n auto`: 1691 passed, 2 skipped.
- `run_lint_imports_check`: PASSED — 9 kept, 0 broken (PyGithub Library Isolation KEPT).
- `run_vulture_check`: no output.

**Status**: pending commit.

**Commit**: `dfc0c82` — `refactor(github_operations): extract exception renderer to fix PyGithub isolation` (4 files, +108/-79).

## Round 3 — 2026-05-12

**Findings** (from engineer subagent running `/implementation_review` focused on the refactor):
- Diff scope confirmed: four files in `dfc0c82` match expectations.
- New `exception_renderer.py`: docstring accurate, function name `render_exception_for_display` descriptive, imports tidy.
- `test_exception_renderer.py`: all five spec cases covered (GithubException with/without/non-dict/whitespace-only message, generic exception, whitespace collapse, 200-char truncation).
- Trimmed `TestUnavailableSection`: three meaningful end-to-end cases remain (GithubException line, generic exception line, multi-section insertion order). Right granularity.
- No duplication between renderer-unit and formatter-end-to-end tests.
- Call site in `pr_feedback.py:87` clean — no leftover `re`/`GithubException` imports.
- Module-level `GithubException` import in `exception_renderer.py` flagged as "Low" — acceptable since the module lives under `github_operations/` (the contract boundary).
- Quality gates: pylint clean, pytest 28/28 passed in target files, mypy clean, lint-imports 9/9 contracts kept.

**Decisions**: accept as-is — no changes warranted.

**Changes**: none.

**Status**: review loop complete (zero code changes this round).

## Final Status

**Rounds**: 3 (Round 1 review of original implementation, Round 2 architectural refactor triggered by import-linter, Round 3 verification of the refactor).
**Commits produced this run**: 1 — `dfc0c82` (`refactor(github_operations): extract exception renderer to fix PyGithub isolation`).
**Implementation**: matches `pr_info/steps/summary.md` end-to-end.
**Quality gates** (final): pylint clean, mypy clean, pytest 1691 passed / 2 skipped, lint-imports 9 kept / 0 broken, vulture no output.
**Outstanding issues**: none.
