# Step 2 — Add `PRFeedback` TypedDict and `get_pr_feedback()` method

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`).
> Implement Step 2 only. Follow TDD: write the tests in `tests/github_operations/test_pr_manager_feedback.py` first, then implement `get_pr_feedback()` and its private helpers in `pr_manager.py`. Run pylint + pytest + mypy and confirm all green. Produce exactly one commit.

## Goal

Add a single public method `PullRequestManager.get_pr_feedback(pr_number)` that fetches:

1. Unresolved review threads + their comments (incl. `diffHunk`) via **one GraphQL query**.
2. Reviews with state `CHANGES_REQUESTED` (also from the same GraphQL query).
3. Top-level conversation comments via REST.
4. Code-scanning alerts via REST (silent skip on 403).

It returns a single `PRFeedback` TypedDict. This is the data layer; formatting happens in Step 3.

## WHERE

- `src/mcp_workspace/github_operations/pr_manager.py` — add `PRFeedback` TypedDict, `get_pr_feedback()` public method, and three private helpers `_fetch_review_data`, `_fetch_conversation_comments`, `_fetch_code_scanning_alerts`.
- `tests/github_operations/test_pr_manager_feedback.py` — new mock-only test file.

## WHAT

### TypedDict

```python
class PRFeedback(TypedDict):
    unresolved_threads: list[dict[str, Any]]    # each: {path, line, author, body, diff_hunk}
    resolved_thread_count: int
    changes_requested: list[dict[str, Any]]     # each: {author, body}
    conversation_comments: list[dict[str, Any]] # each: {author, body}
    alerts: list[dict[str, Any]]                # each: {rule_description, message, path, line}
    unavailable: list[str]                      # section names that failed (not 403): "threads"|"comments"|"alerts"
```

### Public method

```python
@log_function_call
@_handle_github_errors(default_return=cast(PRFeedback, {...empty...}))
def get_pr_feedback(self, pr_number: int) -> PRFeedback:
    ...
```

### Private helpers (module-level or method-private)

```python
def _fetch_review_data(self, pr_number: int) -> tuple[list, int, list]:
    """Single GraphQL → (unresolved_threads, resolved_count, changes_requested_reviews)."""

def _fetch_conversation_comments(self, pr_number: int) -> list[dict]:
    """REST: repo.get_issue(pr_number).get_comments()."""

def _fetch_code_scanning_alerts(self, pr_number: int) -> Optional[list[dict]]:
    """REST: GET /repos/{owner}/{repo}/code-scanning/alerts?ref=refs/pull/{n}/head.
    Returns None on 403 (silent skip), [] on no alerts, list on results."""
```

## HOW

- **GraphQL** — reuse the same plumbing as `get_closing_issue_numbers`:
  ```python
  _, result = self._github_client._Github__requester.graphql_query(
      query=query, variables=variables
  )
  ```
- **REST conversation comments** — use PyGithub: `repo.get_issue(pr_number).get_comments()`.
- **REST code-scanning alerts** — use the raw requester:
  ```python
  status, _, data = self._github_client._Github__requester.requestJsonAndCheck(
      "GET",
      f"/repos/{owner}/{repo}/code-scanning/alerts",
      parameters={"ref": f"refs/pull/{pr_number}/head"},
  )
  ```
  Catch `GithubException` with `status == 403` → return `None` (silent skip per issue decision #2). Other failures → caller appends `"alerts"` to `unavailable`.
- Keep `@_handle_github_errors` decorator on `get_pr_feedback` (matches existing pattern). The 403-silent-skip behaviour for code-scanning is local to `_fetch_code_scanning_alerts`.
- Each private helper wraps its own try/except so that a failure in one section yields the inline placeholder via the `unavailable` list, not a total failure.

## ALGORITHM (`get_pr_feedback` core)

```text
1. validate pr_number; on invalid return empty PRFeedback
2. resolve repo, owner, repo_name
3. unavailable = []
4. try _fetch_review_data → (threads, resolved_count, cr_reviews); except → unavailable += ["threads"]; defaults
5. try _fetch_conversation_comments → comments; except → unavailable += ["comments"]; comments=[]
6. alerts_or_none = _fetch_code_scanning_alerts (returns None on 403)
   if 403 (None): omit silently — leave alerts=[] and do NOT add to unavailable
   on other error: alerts=[]; unavailable += ["alerts"]
7. return PRFeedback(...)
```

### GraphQL query (single call)

```graphql
query($owner: String!, $repo: String!, $prNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      reviewThreads(first: 50) {
        nodes {
          isResolved
          comments(first: 5) {
            nodes { author { login } body path line diffSide diffHunk }
          }
        }
      }
      reviews(first: 50, states: CHANGES_REQUESTED) {
        nodes { state author { login } body submittedAt }
      }
    }
  }
}
```

Post-process: split `reviewThreads.nodes` into `unresolved_threads` (where `isResolved=false`, take first comment's `path/line/author/body/diffHunk`) and `resolved_count` (the rest).

## DATA

Empty `PRFeedback` on validation failure or total error:
```python
{"unresolved_threads": [], "resolved_thread_count": 0, "changes_requested": [],
 "conversation_comments": [], "alerts": [], "unavailable": []}
```

## Tests (write these first — `tests/github_operations/test_pr_manager_feedback.py`)

Mock pattern: mirror `tests/github_operations/test_pr_manager_closing_issues.py` (set up `manager._repository`, `manager._github_client._Github__requester`).

Required test cases:

1. **Happy path** — GraphQL returns 2 unresolved threads + 1 resolved + 1 `CHANGES_REQUESTED` review; REST comments returns 2; code-scanning returns 1 alert. Assert all 4 lists populated correctly.
2. **Clean state** — all sources return empty. Assert all lists empty, `resolved_thread_count == 0`, `unavailable == []`.
3. **403 on code-scanning** — mock `requestJsonAndCheck` to raise `GithubException(status=403, ...)`. Assert `alerts == []` and `"alerts"` is **not** in `unavailable` (silent skip).
4. **500 on code-scanning** — mock raises `GithubException(status=500)`. Assert `alerts == []` and `"alerts" in unavailable`.
5. **GraphQL failure** — mock `graphql_query` raises. Assert `"threads" in unavailable`, lists empty.
6. **Conversation comments failure** — mock `repo.get_issue(...).get_comments()` raises. Assert `"comments" in unavailable`.
7. **Invalid PR number** — `get_pr_feedback(0)` returns empty `PRFeedback`.

## Exit criteria

- pylint passes
- mypy passes (TypedDict shape consistent across all branches)
- pytest passes (new test file green; existing tests untouched)
- One commit on the branch
