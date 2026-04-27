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

### Step 1: Refactor `get_latest_commit_sha()` to Use GitPython
- [ ] Implementation (replace `execute_command` with `safe_repo_context` in `commits.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `refactor: replace execute_command with GitPython in get_latest_commit_sha`

### Step 2: Add `.importlinter` Subprocess Ban Contract
- [ ] Implementation (add forbidden contract banning subprocess in production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `chore: add importlinter subprocess ban for production code`

### Step 3: Clean Up `tach.toml` Subprocess Runner References
- [ ] Implementation (remove all `mcp_coder_utils.subprocess_runner` references from `tach.toml`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `chore: remove stale subprocess_runner dependencies from tach.toml`

## Pull Request
- [ ] Review all changes for correctness and completeness
- [ ] Write PR summary
