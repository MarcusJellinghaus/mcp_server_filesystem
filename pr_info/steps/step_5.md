# Step 5: Register `github_pr_view` and `github_search` Tools in `server.py`

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## LLM Prompt

> Implement Step 5 of issue #78 (see `pr_info/steps/summary.md`).
> Register `github_pr_view` and `github_search` as MCP tools in `server.py`. `github_pr_view` uses `BaseGitHubManager` for raw PyGithub access (reviews, conversation comments, inline review comments). `github_search` uses the PyGithub client's `search_issues()` with auto-scoped `repo:owner/name`. Write tests first (TDD), then implement. Run all code quality checks before committing.

## WHERE

- **Modify**: `src/mcp_workspace/server.py` (add 2 tool functions + imports)
- **Modify**: `tests/github_operations/test_github_read_tools.py` (add tests)
- **Modify**: `vulture_whitelist.py` (add 2 tool names)

## WHAT

### New tool functions in `server.py`

```python
@mcp.tool()
@log_function_call
def github_pr_view(
    number: int,
    include_comments: bool = False,
    max_lines: int = 200,
) -> str:
    """View a GitHub pull request with full detail.

    Args:
        number: PR number to view
        include_comments: Include reviews, conversation and inline comments (default: False)
        max_lines: Maximum output lines (default: 200)

    Returns:
        Formatted PR detail text, or error message string.
    """

@mcp.tool()
@log_function_call
def github_search(
    query: str,
    state: Optional[str] = None,
    labels: Optional[List[str]] = None,
    assignee: Optional[str] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
    max_results: int = 30,
) -> str:
    """Search GitHub issues and pull requests in this repository.

    Automatically scoped to current repository. Additional qualifiers
    can be included inline in the query string (e.g., "fix login author:marcus").

    Args:
        query: Search query text
        state: Filter by state - "open" or "closed"
        labels: Filter by label names
        assignee: Filter by assignee username
        sort: Sort by "comments", "created", or "updated"
        order: Sort order - "asc" or "desc"
        max_results: Maximum results to return (default: 30)

    Returns:
        Compact summary lines, or error message string.
    """
```

## HOW

### `github_pr_view`
- Create `IssueManager(project_dir=_project_dir)` to get a manager with repo access
- Use `manager._get_repository()` for the PyGithub repo object
- Fetch PR: `repo.get_pull(number)` → build dict
- When `include_comments=True`, make 3 additional API calls:
  1. `repo.get_pull(number).get_reviews()` → `List[ReviewData]`
  2. `repo.get_issue(number).get_comments()` → `List[CommentData]` (PRs are issues in GitHub)
  3. `repo.get_pull(number).get_review_comments()` → `List[InlineCommentData]`
- Format via `format_pr_view()`

### `github_search`
- Create `IssueManager(project_dir=_project_dir)` to get authenticated client
- Use `manager._get_repository().full_name` directly for the `repo:owner/name` qualifier
- Build qualifiers dict from named params (`state`, `labels` → comma-joined, `assignee`, `sort`, `order`)
- Call `manager._github_client.search_issues(query=f"repo:{full_name} {query}", **qualifiers)`
- Iterate results up to `max_results`, convert to dicts
- Format via `format_search_results()`

## ALGORITHM

### `github_pr_view`
```
try:
    manager = IssueManager(project_dir=_project_dir)
    repo = manager._get_repository()
    if not repo: return "Error: Could not access repository"
    pr = repo.get_pull(number)
    pr_dict = {number, title, body, state, head_branch, base_branch, ...}
    reviews, conv_comments, inline_comments = None, None, None
    if include_comments:
        reviews = [{user, state, body} for r in pr.get_reviews()]
        conv_comments = [{id, body, user, created_at, ...} for c in repo.get_issue(number).get_comments()]
        inline_comments = [{path, line, user, body} for c in pr.get_review_comments()]
    return format_pr_view(pr_dict, reviews, conv_comments, inline_comments, max_lines)
except Exception as e: return f"Error: {e}"
```

### `github_search`
```
try:
    manager = IssueManager(project_dir=_project_dir)
    repo = manager._get_repository()
    if not repo: return "Error: Could not access repository"
    full_query = f"repo:{repo.full_name} {query}"
    qualifiers = {}  # build from state, labels, assignee, sort, order
    results = manager._github_client.search_issues(full_query, **qualifiers)
    items = []
    for i, item in enumerate(results):
        if i >= max_results: break
        items.append({number, title, state, labels, pull_request: item.pull_request is not None})
    return format_search_results(items, max_results)
except Exception as e: return f"Error: {e}"
```

## DATA

- `github_pr_view` returns: formatted text string (PR detail + optional comments) or `"Error: ..."`
- `github_search` returns: compact summary text with Issue/PR indicators or `"Error: ..."`

## CONFIG CHANGES

### `vulture_whitelist.py` — add 2 more entries

```python
_.github_pr_view
_.github_search
```

## TESTS

In `tests/github_operations/test_github_read_tools.py` (extend file from step 4):

### `github_pr_view`
1. `test_github_pr_view_basic` — returns formatted text with title, state, branches
2. `test_github_pr_view_with_comments` — reviews + conversation + inline comments rendered
3. `test_github_pr_view_without_comments` — no comment sections when `include_comments=False`
4. `test_github_pr_view_not_found` — returns error text on 404
5. `test_github_pr_view_error` — returns `"Error: ..."` on exception

### `github_search`
1. `test_github_search_basic` — returns compact summary lines with auto-scoped repo
2. `test_github_search_empty` — returns "No results found."
3. `test_github_search_with_qualifiers` — verifies state/labels/assignee/sort/order passed through
4. `test_github_search_issue_vs_pr_indicator` — correct Issue/PR indicator in results
5. `test_github_search_max_results_cap` — results capped at max_results
6. `test_github_search_error` — returns `"Error: ..."` on exception

### Test approach
- Mock `IssueManager` constructor and `_get_repository()` / `_github_client`
- For PR view: mock `repo.get_pull()`, `repo.get_issue()`, review/comment iterators
- For search: mock `_github_client.search_issues()` return value
- Verify formatted output contains expected content

## COMMIT

```
feat(github): add github_pr_view and github_search MCP tools (#78)
```
