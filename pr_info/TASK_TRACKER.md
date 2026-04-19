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

### Step 1: Arg Validation Module
- [ ] Implementation: `arg_validation.py` with per-command allowlists + `validate_args()`, and `test_arg_validation.py` with comprehensive unit tests (TDD)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Output Filtering Module
- [ ] Implementation: `output_filtering.py` with `filter_diff_output()`, `filter_log_output()`, `truncate_output()`, and `test_output_filtering.py` with synthetic string tests (TDD)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Read Operations Module
- [ ] Implementation: `read_operations.py` with `git_log()`, `git_diff()`, `git_status()`, `git_merge_base()`, and `test_read_operations.py` with git_integration tests (TDD)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: MCP Server Wrappers + Config Updates
- [ ] Implementation: 4 thin `@mcp.tool()` wrappers in `server.py`, update `tach.toml` and `vulture_whitelist.py`, add server-level tests in `test_server.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
