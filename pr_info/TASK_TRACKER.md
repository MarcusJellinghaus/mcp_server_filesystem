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

### Step 1: Extend `IssueManager.list_issues()` with `labels`, `assignee`, `max_results`
- [x] Implementation: tests + production code in `issues/manager.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(github): extend IssueManager.list_issues with labels, assignee, max_results (#78)`

### Step 2: Create `formatters.py` — Issue Formatters (`format_issue_view`, `format_issue_list`)
- [x] Implementation: tests + production code in `github_operations/formatters.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(github): add issue formatters for view and list tools (#78)`

### Step 3: Add PR and Search Formatters (`format_pr_view`, `format_search_results`)
- [x] Implementation: tests + production code in `github_operations/formatters.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(github): add PR view and search result formatters (#78)`

### Step 4: Register `github_issue_view` and `github_issue_list` Tools in `server.py`
- [x] Implementation: tests + production code in `server.py`, update `tach.toml` and `vulture_whitelist.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(github): add github_issue_view and github_issue_list MCP tools (#78)`

### Step 5: Register `github_pr_view` and `github_search` Tools in `server.py`
- [x] Implementation: tests + production code in `server.py`, update `vulture_whitelist.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(github): add github_pr_view and github_search MCP tools (#78)`

## Pull Request
- [ ] PR review: verify all steps complete, tests pass, no regressions
- [ ] PR summary prepared
