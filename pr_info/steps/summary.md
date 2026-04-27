# Summary: Polling parameters for `check_branch_status` MCP tool

GitHub Issue: #164

## Goal

Add optional polling to the `check_branch_status` MCP tool so callers (mcp-coder skills) can wait for CI to finish and/or for a PR to appear, without re-invoking the tool. Defaults preserve the current one-shot snapshot behavior.

New parameters on the MCP tool (and the underlying public function):

| Param          | Type | Default | Meaning                                           |
|----------------|------|---------|---------------------------------------------------|
| `ci_timeout`   | int  | `0`     | Seconds to poll for CI completion. `0` = no wait. |
| `pr_timeout`   | int  | `0`     | Seconds to poll for PR existence. `0` = no wait.  |
| `wait_for_pr`  | bool | `False` | Enable PR polling. With `pr_timeout=0` → 600s.    |

## Architectural / design changes

**No layer / contract changes.** Polling logic lives in the existing `mcp_workspace.checks.branch_status` module, which already depends on `git_operations`, `github_operations`, and `workflows` (per `tach.toml`). `server.py` stays a thin protocol wrapper.

**Async conversion:**
- The MCP tool `check_branch_status` becomes `async def`.
- A new public `async_poll_branch_status(...)` in `branch_status.py` is the orchestrator. It is importable as a Python library (mcp-coder will adopt it later — see issue follow-up).
- All sync GitHub calls (`CIResultsManager`, `PullRequestManager`, `collect_branch_status`) are wrapped in `asyncio.to_thread()` to keep the MCP event loop free during long waits.

**Polling design (KISS):**
- Two small private helpers — `_wait_for_ci`, `_wait_for_pr` — each ~25 lines, one `while` loop, inline terminal checks. No generic poll abstraction.
- 3 consecutive API errors abort the wait and let the orchestrator do its final `collect_branch_status` (i.e. always return a report, never raise).
- Hardcoded intervals: 15 s for CI, 20 s for PR (matches proven `p_coder` CLI values).

**Execution order in the orchestrator:**
1. If `wait_for_pr=True` OR `ci_timeout > 0`: check `remote_branch_exists()`. If branch is not pushed to origin → skip BOTH waits, run final collection, prepend recommendation `"Push branch to remote before waiting for PR or CI"` via `dataclasses.replace`. The check short-circuits both waits and the recommendation is emitted exactly once.
2. PR wait (if `wait_for_pr=True` and remote branch exists).
3. CI wait (if `ci_timeout > 0` and remote branch exists).
4. One full `collect_branch_status()` via `to_thread`.
5. Return `report.format_for_llm()`.

## Design Decisions

- **Remote-branch check uses `remote_branch_exists()`, NOT `has_remote_tracking_branch()`** — this is a deliberate deviation from the issue's Decisions table. `has_remote_tracking_branch()` only returns True when an upstream is configured (i.e. the user pushed with `git push -u`). If the user pushed without `-u`, an open PR can exist on origin but the local upstream is unset; `has_remote_tracking_branch()` would incorrectly return False and skip both waits. `remote_branch_exists(project_dir, branch)` queries `origin/*` refs directly and proceeds correctly in this scenario.
- **Symmetric guard for CI and PR waits.** If the branch isn't on origin, polling CI is just as wasteful as polling PR — both will fruitlessly time out. A single `remote_branch_exists` lookup gates both, and the same single recommendation covers both cases.
- **`_wait_for_pr` terminal-state is loose.** Any non-empty list from `find_pull_request_by_head` (including closed PRs) is treated as "found". The orchestrator's final `collect_branch_status` surfaces actual PR state to the caller, so this is intentional.

**Backwards compatibility:** All new parameters default to no-wait, so the existing tool surface is preserved bit-for-bit when callers don't pass them.

## Files created or modified

### Modified
- `src/mcp_workspace/checks/branch_status.py`
  - Add module constants: `_CI_POLL_INTERVAL`, `_PR_POLL_INTERVAL`, `_DEFAULT_PR_TIMEOUT`, `_MAX_CONSECUTIVE_ERRORS`.
  - Add private `_wait_for_ci(project_dir, branch_name, timeout)` async helper.
  - Add private `_wait_for_pr(project_dir, branch_name, timeout)` async helper.
  - Add public `async_poll_branch_status(project_dir, max_log_lines, ci_timeout, pr_timeout, wait_for_pr)` orchestrator.
- `src/mcp_workspace/server.py`
  - Convert `check_branch_status` to `async def`.
  - Add `ci_timeout`, `pr_timeout`, `wait_for_pr` parameters.
  - Replace body with `await async_poll_branch_status(...)`.

### Created
- `tests/checks/test_branch_status_polling.py` — unit tests for `_wait_for_ci`, `_wait_for_pr`, and `async_poll_branch_status`. `asyncio.sleep` is patched to keep tests fast.

### Not modified
- `tach.toml`, `.importlinter` — no new dependencies between layers.
- `pyproject.toml` — `pytest-asyncio` is already a dev dep.
- `BranchStatusReport` dataclass — unchanged.
- `collect_branch_status()` — unchanged (called as-is via `to_thread`).

## Step overview

1. **Step 1 — Polling primitives** (`_wait_for_ci`, `_wait_for_pr` + tests)
2. **Step 2 — Orchestrator** (`async_poll_branch_status` + tests)
3. **Step 3 — MCP tool wiring** (`check_branch_status` async signature + tests)
