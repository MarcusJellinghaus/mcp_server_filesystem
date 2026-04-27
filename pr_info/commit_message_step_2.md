feat(checks): add async_poll_branch_status orchestrator

Add public async function in branch_status.py that optionally polls
for CI completion and PR existence before producing the final report.

Defaults reproduce the current snapshot behavior (no waiting). When
wait_for_pr or ci_timeout > 0 is requested, a single
remote_branch_exists lookup gates both waits and emits a single
"Push branch to remote before waiting for PR or CI" recommendation
when the branch isn't on origin. PR wait runs before CI wait; final
collect_branch_status is always invoked via asyncio.to_thread.

Tests cover defaults, explicit timeouts, default PR timeout fallback,
remote-branch absence (PR-only, CI-only, both), execution order, and
the no-branch early-return path.
