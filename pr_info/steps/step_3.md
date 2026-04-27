# Step 3 — Wire MCP tool `check_branch_status` to the orchestrator

**Reference:** [summary.md](./summary.md) — see "Files created or modified".

**Depends on:** Step 2 (`async_poll_branch_status` must exist).

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`).
> Convert the `check_branch_status` MCP tool in `src/mcp_workspace/server.py` to async and add the three new optional parameters. Follow TDD: extend `tests/test_server.py` with a new test first, then update the tool, then ensure all checks pass. One commit.

## WHERE

- **Production:** `src/mcp_workspace/server.py` — modify the existing `check_branch_status` tool function (currently at the bottom of the file, sync, takes only `max_log_lines`).
- **Tests:** extend `tests/test_server.py` with one new test (or class).

## WHAT

Replace the current sync tool:

```python
@mcp.tool()
@log_function_call
async def check_branch_status(
    max_log_lines: int = 300,
    ci_timeout: int = 0,
    pr_timeout: int = 0,
    wait_for_pr: bool = False,
) -> str:
    """Check comprehensive branch status: git state, CI, PR, tasks.

    Args:
        max_log_lines: Maximum CI log lines to include (default 300).
        ci_timeout: Seconds to poll for CI completion. 0 disables polling (default).
        pr_timeout: Seconds to poll for PR existence. 0 disables polling (default).
        wait_for_pr: Enable PR polling. With pr_timeout=0 falls back to 600s.

    Returns:
        Formatted branch status report for LLM consumption.
    """
    if _project_dir is None:
        raise ValueError("Project directory has not been set")
    return await async_poll_branch_status(
        _project_dir,
        max_log_lines=max_log_lines,
        ci_timeout=ci_timeout,
        pr_timeout=pr_timeout,
        wait_for_pr=wait_for_pr,
    )
```

## HOW

- Update the import in `server.py`:
  - Remove `from mcp_workspace.checks.branch_status import collect_branch_status`.
  - Replace with `from mcp_workspace.checks.branch_status import async_poll_branch_status`.
- Decorators stay in the same order: `@mcp.tool()` first, then `@log_function_call`.
- No other tool in `server.py` is touched.

## ALGORITHM

Trivial wiring — just parameter pass-through. No logic.

## DATA

- Signature: same return type (`str`) as before; three new optional parameters with safe defaults preserving snapshot behavior.

## Tests (write first — TDD)

Extend `tests/test_server.py`:

1. **`test_check_branch_status_defaults`** (async, `pytest.mark.asyncio`):
   - Patch `mcp_workspace.server.async_poll_branch_status` with `AsyncMock` returning a known string.
   - Set `_project_dir` (use existing fixture pattern in the file).
   - Call `await check_branch_status()`.
   - Assert the mock was awaited once with `(_project_dir, max_log_lines=300, ci_timeout=0, pr_timeout=0, wait_for_pr=False)`.
   - Assert return value matches the mock's return.

2. **`test_check_branch_status_with_polling_params`** (async):
   - Same setup; call with `await check_branch_status(max_log_lines=100, ci_timeout=180, pr_timeout=600, wait_for_pr=True)`.
   - Assert kwargs propagate correctly.

3. **`test_check_branch_status_no_project_dir`**:
   - Reset `_project_dir` to `None`.
   - Assert `ValueError` is raised.

(Look up how `tests/test_server.py` currently sets/resets `_project_dir` and follow that pattern.)

## Definition of done

- All three new tests pass.
- All existing tests still pass — including any prior `check_branch_status` tests; if they relied on `collect_branch_status` directly through `server.py`, update them to mock `async_poll_branch_status` instead.
- All three MCP code-quality checks green.
- Manual sanity check via search: no remaining usage of `collect_branch_status` in `server.py`.
- One commit: `feat(server): expose polling params on check_branch_status MCP tool`.
