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

### Step 1: Add tests and implement auto_delete_branches check
- [x] Implementation: add tests for check 10 + update `_patch_all_ok` helper + implement check 10 in `verification.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat: add auto_delete_branches check to verify_github (#162)`

## Pull Request
- [x] Review all changes for correctness and completeness
- [ ] Write PR summary
