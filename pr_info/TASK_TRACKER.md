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

### Step 1: Add `is_path_in_git_dir()` Helper and DRY-Refactor `_discover_files()`
- [ ] Implementation: tests for `is_path_in_git_dir()` + function + refactor `_discover_files()` to use it
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Add `is_path_gitignored()` Utility Function
- [ ] Implementation: tests for `is_path_gitignored()` + function in `directory_utils.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Enforce Gitignore in All Server File Tools
- [ ] Implementation: tests for gitignore enforcement + `_check_not_gitignored()` guard in `server.py` + enforce in 6 tool handlers
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps integrated correctly, no regressions
- [ ] PR summary prepared
