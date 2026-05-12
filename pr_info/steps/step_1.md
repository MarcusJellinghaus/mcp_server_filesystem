# Step 1 — Change `PRFeedback.unavailable` data shape

## LLM Prompt

Read `pr_info/steps/summary.md` for full context, then implement Step 1 as described in this file.

**Apply TDD:** update the tests first to express the new dict shape, then update the production code so they pass. After implementation, run all three code-quality checks (pylint, pytest, mypy) and ensure they pass before committing.

**Out of scope for this step:** do **not** modify `format_pr_feedback()` or write rendering tests for exception detail — that is Step 2. The user-visible output (`[unavailable] threads: API error`) must remain identical after this step. Tests in `TestUnavailableSection` keep their current assertions; only the fixture construction changes.

---

## WHERE

| File | Change |
| ---- | ------ |
| `src/mcp_workspace/github_operations/pr_manager.py` | TypedDict + `_empty_pr_feedback` + 3 sites in `get_pr_feedback` |
| `tests/github_operations/test_pr_manager_feedback.py` | Assertion updates |
| `tests/checks/test_branch_status_pr_feedback.py` | `_empty_feedback` helper + `TestUnavailableSection` fixtures (assertions unchanged) |

## WHAT

### Production code — `pr_manager.py`

#### `PRFeedback` TypedDict (lines ~42-50)

```python
class PRFeedback(TypedDict):
    unresolved_threads: list[dict[str, Any]]
    resolved_thread_count: int
    changes_requested: list[dict[str, Any]]
    conversation_comments: list[dict[str, Any]]
    alerts: list[dict[str, Any]]
    unavailable: dict[str, Exception]   # ← changed from list[str]
```

#### `_empty_pr_feedback()` (lines ~53-62)

```python
def _empty_pr_feedback() -> PRFeedback:
    return {
        "unresolved_threads": [],
        "resolved_thread_count": 0,
        "changes_requested": [],
        "conversation_comments": [],
        "alerts": [],
        "unavailable": {},   # ← was []
    }
```

#### `get_pr_feedback()` (lines ~540-585)

- Change local declaration: `unavailable: dict[str, Exception] = {}` (was `list[str] = []`).
- Replace each of the three `unavailable.append("X")` calls in the per-section `except` blocks with `unavailable["X"] = e`:
  - threads section: `unavailable["threads"] = e`
  - comments section: `unavailable["comments"] = e`
  - alerts section: `unavailable["alerts"] = e`
- `logger.warning(...)` calls remain unchanged.
- Update `get_pr_feedback`'s docstring (line ~535): the current text says the returned `unavailable` is `"a list of section names that failed to fetch"`. Replace with a description of the new return shape — a dict mapping failed section names to the raised exception, with the same exclusion of 403-on-alerts (still silently skipped, not recorded as unavailable).

## HOW

- No new imports.
- `_handle_github_errors` decorator on `get_pr_feedback` — untouched.
- No public API change (no re-exports).
- The formatter loop `for section in unavailable:` continues to work in this step (iterating a dict yields keys, still strings), so the `format_pr_feedback` source is **not** modified here.

## ALGORITHM

N/A — pure data-shape refactor.

## DATA

`PRFeedback.unavailable` is now `dict[str, Exception]`. Keys are section names; values are the raw exception caught in the corresponding `try/except` block. Empty dict when all sources succeeded.

Examples:
- All sources OK → `{}`
- Threads + comments failed → `{"threads": GithubException(500, ...), "comments": ConnectionError(...)}`

---

## Test Updates

### `tests/github_operations/test_pr_manager_feedback.py`

- `test_happy_path` → `assert result["unavailable"] == {}` (was `== []`)
- `test_clean_state` → `assert result["unavailable"] == {}`
- `test_invalid_pr_number` → `assert result["unavailable"] == {}`
- `test_code_scanning_403_silent_skip` → `assert "alerts" not in result["unavailable"]` (works on dicts unchanged)
- `test_code_scanning_500_unavailable` → keep `assert "alerts" in result["unavailable"]`; **add** `assert isinstance(result["unavailable"]["alerts"], GithubException)`
- `test_graphql_failure` → keep `assert "threads" in result["unavailable"]`; **add** `assert isinstance(result["unavailable"]["threads"], GithubException)`
- `test_conversation_comments_failure` → keep `assert "comments" in result["unavailable"]`; **add** `assert isinstance(result["unavailable"]["comments"], GithubException)`

### `tests/checks/test_branch_status_pr_feedback.py`

- `_empty_feedback` helper → `"unavailable": {}`
- `TestUnavailableSection.test_unavailable_threads_placeholder` → change fixture to a dict with any throwaway exception value (e.g., `Exception("boom")`); assertion `assert "[unavailable] threads: API error" in result` **stays the same** (formatter still emits the hardcoded suffix in this step).
- `TestUnavailableSection.test_unavailable_multiple_sections` → fixture becomes `{"threads": Exception("a"), "comments": Exception("b")}`; assertions unchanged.

---

## Verification

Run via MCP tools (see `.claude/CLAUDE.md` for required flags):

- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
- `mcp__mcp-tools-py__run_mypy_check`

All three must pass before committing.

## Commit

One commit covering all four files. Suggested message:

```
refactor(pr_feedback): store exceptions in PRFeedback.unavailable

Change PRFeedback.unavailable from list[str] to dict[str, Exception]
to carry per-section error detail to the formatter. No user-visible
output change in this step; format_pr_feedback still emits the
hardcoded 'API error' suffix.

Refs #199
```
