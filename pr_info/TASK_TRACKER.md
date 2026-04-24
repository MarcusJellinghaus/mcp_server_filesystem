# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Rewrite utility function and its tests
- [x] Implementation: rewrite `edit_file` in `edit_file.py` with new signature, rewrite `test_edit_file.py` (TDD)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Rewrite server tool and its tests
- [x] Implementation: rewrite `edit_file` MCP tool in `server.py` (async + locking), rewrite `test_edit_file_api.py` (TDD)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Migrate remaining test files
- [x] Implementation: migrate `test_edit_file_issues.py`, `test_edit_already_applied_fix.py`, `test_edit_file_backslash.py` to new interface
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Final verification and cleanup
- [x] Implementation: verify `__init__.py` exports, vulture whitelist, run all checks, fix any remaining issues
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request
- [x] PR review: verify all steps complete, diff is clean
- [ ] PR summary prepared
