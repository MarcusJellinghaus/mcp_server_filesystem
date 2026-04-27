feat(checks): add async polling primitives for branch status

Add two private async helpers in mcp_workspace.checks.branch_status:
_wait_for_ci polls CI status until terminal (success/failure) or
timeout, _wait_for_pr polls find_pull_request_by_head until a PR is
found or timeout.

Both helpers wrap the sync GitHub APIs in asyncio.to_thread, abort
after _MAX_CONSECUTIVE_ERRORS (3) consecutive errors, and emit a
single info log on entry plus one on terminal state, with warnings
only on exception. Add module constants _CI_POLL_INTERVAL (15s),
_PR_POLL_INTERVAL (20s), _DEFAULT_PR_TIMEOUT (600s), and
_MAX_CONSECUTIVE_ERRORS (3).

Tests in tests/checks/test_branch_status_polling.py cover terminal
states, timeout exit, error tolerance, error-driven abort, and the
timeout=0 short-circuit. asyncio.sleep is patched so tests run
instantly.
