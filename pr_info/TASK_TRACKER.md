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

### Step 1: Add `normalize_line_endings` to `path_utils.py`
- [ ] Implementation: add function to `path_utils.py`, remove legacy copy from `edit_file.py`, move tests to `test_path_utils.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat: add normalize_line_endings to path_utils`

### Step 2: Normalize CRLF in `save_file` / `append_file`
- [ ] Implementation: normalize in `_validate_save_parameters`, refactor `append_file` to use it, add CRLF tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `fix: normalize CRLF in save_file/append_file`

### Step 3: Normalize CRLF in `edit_file`
- [ ] Implementation: normalize `original_content`, `old_text`, `new_text` in `edit_file`, add CRLF tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `fix: normalize CRLF in edit_file`

## Pull Request
- [ ] PR review completed
- [ ] PR summary prepared
