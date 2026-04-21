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

### Step 1: Rename "matches" key to "details" in search results
- [ ] Implementation: rename `"matches"` → `"details"` in `_search_content()` and update all test assertions
- [ ] Quality checks pass: pylint, pytest, mypy
- [ ] Commit: `refactor: rename "matches" key to "details" in search results`

### Step 2: Add per-line truncation (500 char cap)
- [ ] Implementation: add `_MAX_LINE_CHARS` constant and truncation logic in `_search_content()`, add tests for long-line truncation
- [ ] Quality checks pass: pylint, pytest, mypy
- [ ] Commit: `feat: add per-line truncation to search content results`

### Step 3: Add character budget and compact fallback
- [ ] Implementation: replace line-counting with char budget (`max_result_lines * 120`), add `matched_files` compact fallback when truncated, add/update tests
- [ ] Quality checks pass: pylint, pytest, mypy
- [ ] Commit: `feat: add char budget and compact fallback for large search results`

## Pull Request
- [ ] PR review: all steps complete, all checks green
- [ ] PR summary prepared
