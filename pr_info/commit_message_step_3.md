feat(server): expose polling params on check_branch_status MCP tool

Convert the check_branch_status MCP tool to async def and add three
new optional parameters: ci_timeout, pr_timeout, and wait_for_pr.
The body now delegates to async_poll_branch_status, which handles
remote-branch gating and the optional PR/CI polling loops.

Defaults preserve the prior one-shot snapshot behavior bit-for-bit.
The collect_branch_status import is replaced with async_poll_branch_status.

Tests cover the default invocation, propagation of polling kwargs,
and the missing-project-directory error path, all using AsyncMock
to patch async_poll_branch_status.
