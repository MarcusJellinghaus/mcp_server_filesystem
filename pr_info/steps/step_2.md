# Step 2 — `async_poll_branch_status` orchestrator

**Reference:** [summary.md](./summary.md) — see "Execution order in the orchestrator".

**Depends on:** Step 1 (private helpers `_wait_for_ci`, `_wait_for_pr` must exist).

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`).
> Implement the public async orchestrator `async_poll_branch_status` in `src/mcp_workspace/checks/branch_status.py`. Follow TDD: extend `tests/checks/test_branch_status_polling.py` with a new test class first, then the implementation, then ensure all checks pass. One commit.

## WHERE

- **Production:** `src/mcp_workspace/checks/branch_status.py` — add public function below the private helpers from Step 1.
- **Tests:** extend `tests/checks/test_branch_status_polling.py` with a new `TestAsyncPollBranchStatus` class.

## WHAT

Public async function:

```python
async def async_poll_branch_status(
    project_dir: Path,
    max_log_lines: int = 300,
    ci_timeout: int = 0,
    pr_timeout: int = 0,
    wait_for_pr: bool = False,
) -> str:
    """Collect branch status, optionally polling for CI/PR.

    Returns the report formatted via `format_for_llm()`.
    """
```

Defaults reproduce the current snapshot behavior (no waiting).

## HOW

- Add `from dataclasses import replace` import (only if not already present).
- Use existing `mcp_workspace.git_operations.branch_queries.remote_branch_exists` —
  add it to the existing branch_queries import block at top of `branch_status.py`.
  (Deliberate deviation from the issue Decisions table — see `summary.md` "Design Decisions". `remote_branch_exists` correctly handles users who pushed without `-u`.)
- Use existing `mcp_workspace.git_operations.branch_queries.get_current_branch_name`
  (already imported) to obtain the branch name once at the top of the orchestrator.
- Wrap `collect_branch_status(project_dir, max_log_lines=max_log_lines)` in
  `await asyncio.to_thread(...)`.
- Wrap `remote_branch_exists(project_dir, branch_name)` in
  `await asyncio.to_thread(...)`.

## ALGORITHM

```
branch = await to_thread(get_current_branch_name, project_dir)

# Early-return path when not in a git repo — skip both waits AND
# skip the remote_branch_exists lookup entirely (must NOT be called
# when branch is None).
if branch is None:
    report = await to_thread(collect_branch_status, project_dir, max_log_lines)
    return report.format_for_llm()

# Single remote-branch lookup gates BOTH PR-wait and CI-wait.
# Reached ONLY when branch is not None (guaranteed by early-return above).
needs_remote = wait_for_pr or ci_timeout > 0
remote_present = (
    await to_thread(remote_branch_exists, project_dir, branch)
    if needs_remote
    else True
)

skip_msg = None
if needs_remote and not remote_present:
    skip_msg = "Push branch to remote before waiting for PR or CI"
else:
    if wait_for_pr:
        effective_pr_timeout = pr_timeout if pr_timeout > 0 else _DEFAULT_PR_TIMEOUT
        await _wait_for_pr(project_dir, branch, effective_pr_timeout)
    if ci_timeout > 0:
        await _wait_for_ci(project_dir, branch, ci_timeout)

report = await to_thread(collect_branch_status, project_dir, max_log_lines)

if skip_msg:
    report = replace(report, recommendations=[skip_msg, *report.recommendations])

return report.format_for_llm()
```

Notes:
- The remote-branch check short-circuits BOTH PR-wait and CI-wait. We only emit the
  recommendation once even if both `wait_for_pr` and `ci_timeout > 0` were requested.
- `_wait_for_pr` terminal state = `find_pull_request_by_head` returns a non-empty list
  (any state, including closed). This is deliberate: an existing PR — even if closed —
  is the signal to stop waiting; the orchestrator's final `collect_branch_status`
  surfaces the actual PR state to the caller.

## DATA

- Returns: `str` — output of `BranchStatusReport.format_for_llm()`.
- No new types. Reuses existing `BranchStatusReport`.

## Tests (write first — TDD)

Extend `tests/checks/test_branch_status_polling.py` with `TestAsyncPollBranchStatus`:

Patch `_wait_for_ci`, `_wait_for_pr`, `collect_branch_status`, `remote_branch_exists`,
and `get_current_branch_name` (all in `mcp_workspace.checks.branch_status`).
Build a fixture `BranchStatusReport` returned by the patched `collect_branch_status`.

Test cases:

1. **Defaults** (`wait_for_pr=False`, both timeouts `0`): neither helper is called; `remote_branch_exists` NOT called (no need to look it up); `collect_branch_status` is called once; output equals `format_for_llm()` of the fixture report.
2. **`ci_timeout=30`, remote branch exists**: `_wait_for_ci` called with `(project_dir, branch, 30)`; `_wait_for_pr` not called.
3. **`wait_for_pr=True`, remote branch exists, default PR timeout**: import `_DEFAULT_PR_TIMEOUT` directly from `mcp_workspace.checks.branch_status`; assert `_wait_for_pr` was awaited with `(project_dir, branch, _DEFAULT_PR_TIMEOUT)`. Recommendation NOT prepended. (NOTE: do NOT assert on `asyncio.sleep` interval or elapsed virtual-time here — `_wait_for_pr` is patched at the orchestrator level, so its internals never execute. Interval/timeout-elapsed assertions belong in Step 1's `TestWaitForPR`.)
4. **`wait_for_pr=True`, `pr_timeout=120`, remote branch exists**: `_wait_for_pr` called with `120`.
5. **`wait_for_pr=True`, no remote branch**: `_wait_for_pr` NOT called; output recommendations include `"Push branch to remote before waiting for PR or CI"` as the FIRST entry (verify via the un-formatted `BranchStatusReport` returned by `replace(...)` or by string-contains on `format_for_llm()` output).
6. **`ci_timeout=30`, no remote branch**: `_wait_for_ci` NOT called; recommendation `"Push branch to remote before waiting for PR or CI"` prepended.
7. **Both flags, no remote branch**: neither helper called; recommendation prepended exactly ONCE (not duplicated).
8. **Order check**: when both `wait_for_pr=True` and `ci_timeout>0` and remote branch exists, `_wait_for_pr` is awaited before `_wait_for_ci`, and `collect_branch_status` runs after both. Use a list captured by side-effects to assert order.
9. **No branch** (`get_current_branch_name` returns `None`): neither helper nor `remote_branch_exists` called; report still produced.

## Definition of done

- New tests in `TestAsyncPollBranchStatus` pass.
- All existing tests still pass.
- All three MCP code-quality checks green.
- One commit: `feat(checks): add async_poll_branch_status orchestrator`.
