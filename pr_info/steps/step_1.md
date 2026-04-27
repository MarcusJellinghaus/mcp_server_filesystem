# Step 1 — Polling primitives `_wait_for_ci` and `_wait_for_pr`

**Reference:** [summary.md](./summary.md) — see "Polling design (KISS)" and "Execution order".

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`).
> Implement the two private async polling helpers in `src/mcp_workspace/checks/branch_status.py`, following TDD: write the failing tests first in `tests/checks/test_branch_status_polling.py`, then the implementation, then ensure all checks pass. One commit for the whole step.

## WHERE

- **Production:** `src/mcp_workspace/checks/branch_status.py` — add new module constants and two private async helpers at the bottom of the file (after `collect_branch_status`).
- **Tests (new file):** `tests/checks/test_branch_status_polling.py`.

## WHAT

Add module-level constants near the top (next to `DEFAULT_LABEL`):

```python
_CI_POLL_INTERVAL = 15
_PR_POLL_INTERVAL = 20
_DEFAULT_PR_TIMEOUT = 600
_MAX_CONSECUTIVE_ERRORS = 3
```

Two private async functions:

```python
async def _wait_for_ci(
    project_dir: Path, branch_name: str, timeout: int
) -> None:
    """Poll CI status until terminal (success/failure) or timeout."""

async def _wait_for_pr(
    project_dir: Path, branch_name: str, timeout: int
) -> None:
    """Poll for PR existence until found or timeout."""
```

Both are fire-and-forget (return `None`) — they only block until terminal/timeout. The orchestrator (Step 2) does a fresh `collect_branch_status` afterwards to read final state.

## HOW

- Use `import asyncio` and `import time` (already imported `logging`) at the top of the file.
- Use `await asyncio.to_thread(...)` to call sync GitHub APIs:
  - CI: `CIResultsManager(project_dir=project_dir).get_latest_ci_status(branch_name)`
  - PR: `PullRequestManager(project_dir).find_pull_request_by_head(branch_name)`
- Use `await asyncio.sleep(interval)` between iterations.
- `time.monotonic()` for the deadline; abort when `time.monotonic() >= deadline`.
- Catch `Exception` around each `to_thread` call; track `consecutive_errors`; reset to 0 on success; abort when it hits `_MAX_CONSECUTIVE_ERRORS`. Log via `logger.info` / `logger.warning`.
- No new imports outside the module — `CIResultsManager` and `PullRequestManager` are already imported.

## ALGORITHM

```
deadline = time.monotonic() + timeout
errors = 0
while time.monotonic() < deadline:
    try:
        result = await asyncio.to_thread(<sync API call>)
        errors = 0
        if <terminal check>:
            return
    except Exception:
        errors += 1
        logger.warning(...)
        if errors >= _MAX_CONSECUTIVE_ERRORS:
            return
    await asyncio.sleep(<interval>)
```

Terminal checks (inlined, no helper):
- CI: `(run := result.get("run")) and run.get("conclusion") in ("success", "failure")`
- PR: `result` (truthy non-empty list)

## DATA

Both helpers: return `None`. Side effects: time elapsed + log lines. State is read afterwards via the orchestrator's `collect_branch_status` call (Step 2).

## Tests (write first — TDD)

New file: `tests/checks/test_branch_status_polling.py`

Use `pytest.mark.asyncio`. Patch `asyncio.sleep` with `AsyncMock` (so tests run instantly). Patch `CIResultsManager` and `PullRequestManager` from `mcp_workspace.checks.branch_status` (where they're imported).

Test cases (one class per helper):

`TestWaitForCI`:
- Returns immediately when first poll yields `conclusion="success"`.
- Returns immediately when first poll yields `conclusion="failure"`.
- Returns after timeout when status stays `"in_progress"`.
- Tolerates 2 consecutive exceptions, then succeeds on 3rd call.
- Aborts (returns) after 3 consecutive exceptions.
- `timeout=0` returns immediately without polling.

`TestWaitForPR`:
- Returns immediately when first poll returns a non-empty list.
- Returns after timeout when polls keep returning `[]`.
- Aborts after 3 consecutive exceptions.
- `timeout=0` returns immediately without polling.

Assertions: `to_thread` mock call counts, helper return value (`None`), test runtime (sleep patched).

## Definition of done

- `tests/checks/test_branch_status_polling.py` exists, all new tests pass.
- All existing tests still pass.
- `mcp__tools-py__run_pytest_check`, `run_pylint_check`, `run_mypy_check` all green.
- One commit: `feat(checks): add async polling primitives for branch status`.
