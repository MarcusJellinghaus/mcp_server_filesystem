# Step 1 — Add `mergeable_state` to `PullRequestData`

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`).
> Implement Step 1 only. Follow TDD: write/extend the tests first, then update the production code, then run pylint + pytest + mypy and confirm all green. Produce exactly one commit for this step.

## Goal

Add a new `mergeable_state` field to the `PullRequestData` TypedDict and populate it in every PR-builder method in `PullRequestManager`. This is a small, self-contained change that establishes the new field used by the report in Step 4.

## WHERE

- `src/mcp_workspace/github_operations/pr_manager.py` — modify `PullRequestData` TypedDict and the 5 builder methods.
- `tests/github_operations/test_pr_manager.py` — extend existing tests with assertions on the new field for `create_pull_request`, `get_pull_request`, `list_pull_requests`, and `close_pull_request`.
- `tests/github_operations/test_pr_manager_find_by_head.py` — extend existing tests with the `mergeable_state` assertion for `find_pull_request_by_head` (this builder lives in a separate test file from the others above).

## WHAT

### TypedDict change

```python
class PullRequestData(TypedDict):
    ...existing fields...
    mergeable_state: Optional[str]   # NEW: GitHub's mergeable_state ("clean", "dirty", "unstable", "blocked", etc.)
```

### Builders to update (each adds one key to the returned dict)

| Method | Population |
|--------|------------|
| `create_pull_request` | `"mergeable_state": pr.mergeable_state` |
| `get_pull_request` | `"mergeable_state": pr.mergeable_state` |
| `list_pull_requests` | `"mergeable_state": pr.mergeable_state` |
| `find_pull_request_by_head` | `"mergeable_state": pr.mergeable_state` |
| `close_pull_request` | `"mergeable_state": updated_pr.mergeable_state` |

## HOW

- PyGithub's `PullRequest` object exposes `pr.mergeable_state` as a string. No new imports.
- The field is `Optional[str]` because PyGithub may return `None` while GitHub computes the state.
- No changes to `BaseGitHubManager`, decorators, or any other module in this step.

## ALGORITHM

No new algorithm — just add `"mergeable_state": pr.mergeable_state` to each existing return dict.

## DATA

`PullRequestData` gains one optional string field. All call sites already use `.get(...)` access patterns or pass dicts whole, so no caller-site changes are required in this step.

## Tests (write these first)

In `tests/github_operations/test_pr_manager.py`:

1. Where existing tests construct a `create_mock_pr` (or equivalent) for `get_pull_request`, `create_pull_request`, `list_pull_requests`, `close_pull_request`, set `mock_pr.mergeable_state = "clean"` and assert `result["mergeable_state"] == "clean"`.
2. Add one parameterised test verifying `mergeable_state` flows through for values: `"clean"`, `"dirty"`, `"unstable"`, `"blocked"`, `None`.

For `find_pull_request_by_head`, extend the equivalent test in `tests/github_operations/test_pr_manager_find_by_head.py` (single new assertion in the existing success test).

## Exit criteria

- pylint passes
- mypy passes (the TypedDict change must be reflected in every builder)
- pytest passes (existing tests still green; new assertions green)
- One commit on the branch
