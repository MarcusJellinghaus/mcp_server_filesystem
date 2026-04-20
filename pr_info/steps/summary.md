# Issue #78: Add Read-Only GitHub API Tools (Issue/PR View, List, Search)

## Goal

Add 4 read-only MCP tools for reading GitHub issues and pull requests, using existing PyGithub infrastructure. All tools are project-scoped (derive repo from git remote).

## Tools

| Tool | Purpose | Default Comments |
|------|---------|-----------------|
| `github_issue_view` | View single issue with detail | `include_comments=True` |
| `github_pr_view` | View single PR with detail | `include_comments=False` |
| `github_issue_list` | List/filter issues (summary lines) | N/A |
| `github_search` | Search issues/PRs (summary lines) | N/A |

## Architecture / Design Changes

### New file
- **`src/mcp_workspace/github_operations/formatters.py`** — Pure formatting functions (text in → text out). No API calls. Keeps `server.py` thin and formatters independently testable.

### Modified files
- **`src/mcp_workspace/github_operations/issues/manager.py`** — Extend `list_issues()` and `_list_issues_no_error_handling()` with `labels`, `assignee`, `max_results` parameters (all natively supported by PyGithub's `repo.get_issues()`).
- **`src/mcp_workspace/server.py`** — Register 4 new MCP tool functions. Each creates a manager, fetches data, formats via `formatters.py`, catches exceptions → returns error as text string.
- **`tach.toml`** — Add `mcp_workspace.github_operations` to `server` module's `depends_on`.
- **`vulture_whitelist.py`** — Add 4 new tool function names.

### New test files
- **`tests/github_operations/test_formatters.py`** — Pure function tests for all 4 formatters (truncation, empty input, edge cases). No mocking needed.
- **`tests/github_operations/test_github_read_tools.py`** — Tests for the 4 MCP tool functions in `server.py` with mocked managers. Verifies error-as-text, parameter pass-through, `max_lines` truncation.

### Unchanged files (reused as-is)
- `BaseGitHubManager` — Used directly for `github_pr_view` and `github_search` (raw PyGithub calls via `_get_repository()` and `_github_client`).
- `PullRequestManager` — **Not modified**. PR view fetches data via raw PyGithub on the repo object instead.
- `github_utils.py` (`parse_github_url`, `get_repo_full_name`) — Reused for search auto-scoping.

### Design decisions
1. **Error handling**: Tool functions catch exceptions and return error text strings (e.g., `"Error: Issue #999 not found"`). Does NOT rely on `_handle_github_errors` decorator's silent defaults.
2. **PR comments via raw PyGithub**: `github_pr_view` with `include_comments=True` makes 3 API calls directly on the repo object — reviews, conversation comments (via Issues API), and inline review comments. No new methods added to `PullRequestManager`.
3. **Search auto-scoping**: `github_search` prepends `repo:owner/name` derived from git remote.
4. **No cache layer**: All tools fetch fresh data per call via PyGithub.
5. **`max_lines` truncation**: Applied in formatters with "... truncated, N lines total" indicator.
6. **`max_results` cap**: Applied with "refine your query" guidance when results are truncated.

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Extend `IssueManager.list_issues()` with `labels`, `assignee`, `max_results` | Tests + implementation |
| 2 | Create `formatters.py` with `format_issue_view` and `format_issue_list` | Tests + implementation |
| 3 | Create `formatters.py` additions: `format_pr_view` and `format_search_results` | Tests + implementation |
| 4 | Register `github_issue_view` and `github_issue_list` tools in `server.py` | Tests + implementation + config |
| 5 | Register `github_pr_view` and `github_search` tools in `server.py` | Tests + implementation + config |
