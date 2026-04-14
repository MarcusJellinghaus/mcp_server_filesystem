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

### Step 1: Add read_github_deps.py with tests
- [x] Implementation: create `tools/read_github_deps.py` (verbatim from reference) and `tests/test_read_github_deps.py` (from scratch)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat: add read_github_deps.py with tests`

### Step 2: Rewrite reinstall_local.bat to match modern pattern
- [ ] Implementation: rewrite `tools/reinstall_local.bat` following 0-6 step template from reference
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat: rewrite reinstall_local.bat to match modern pattern`

## Pull Request
- [ ] PR review: verify all steps complete and checks pass
- [ ] PR summary prepared
