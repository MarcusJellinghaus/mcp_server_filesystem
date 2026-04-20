# Implementation Review Log — Issue #78

## Overview
Add read-only GitHub API tools (issue/PR view, list, search)

---

## Round 1 — 2026-04-20
**Findings**:
1. [Skip] `github_search` qualifiers pattern slightly fragile — works correctly, speculative concern
2. [Skip] Protected access on `_get_repository()` — acknowledged with pylint disable, design decision
3. [Skip] IssueManager used for PR data — documented design decision
4. [Accept] `line=None` prints "None" in inline comment formatting (formatters.py:147)
5. [Skip] `number == 0` sentinel — GitHub numbers start at 1, safe
6. [Skip] Labels as comma-separated string — works with GitHub search syntax
7. [Skip] No sort/order validation — exception handler makes it safe
8. [Skip] `_project_dir` could be None — error path works correctly
9. [Skip] Implicit contract between search/formatter — works correctly
10. [Accept] Mixed `Dict`/`list` style in formatters.py — Python 3.11+, Boy Scout fix

**Decisions**:
- Accepted #4: cosmetic bug showing "None" instead of meaningful placeholder
- Accepted #10: modernize type hints consistently (project is Python 3.11+)
- Skipped all others: speculative, pre-existing design decisions, or already safe

**Changes**:
- `formatters.py`: replaced `Dict`/`List` imports with built-in `dict`/`list`
- `formatters.py`: added None-safe check for inline comment line number (displays "?" instead of "None")

**Status**: Committed as `da74dde` — `fix(github): use modern type hints and handle None inline comment line (#78)`

## Round 2 — 2026-04-20
**Findings**: None. Re-review confirmed fixes are correct.
**Decisions**: N/A
**Changes**: None
**Status**: No changes needed

## Final Status
- **Rounds**: 2 (1 with changes, 1 clean)
- **Commits**: 1 fix commit
- **Issues remaining**: None
- **All quality checks pass**: pylint, pytest (1054 passed), mypy

