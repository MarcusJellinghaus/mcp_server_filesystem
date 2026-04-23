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

### Step 1: Add `@log_function_call` to `git()` in server.py
- [ ] Implementation: add decorator to `git()` async function
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(logging): add @log_function_call to git() async wrapper (#142)`

### Step 2: Add `@log_function_call` to 3 async reference tools, remove manual debug logging
- [ ] Implementation: add decorator to `read_reference_file()`, `list_reference_directory()`, `search_reference_files()`; remove 2 manual `logger.debug` calls; rename test `test_log_function_call_removed` → `test_async_handlers_are_coroutines`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(logging): add @log_function_call to async reference tools (#142)`

## Pull Request
- [ ] PR review: verify all steps complete, diff looks correct
- [ ] PR summary prepared
