---
description: Approve implementation plan and transition to plan-ready status
disable-model-invocation: true
allowed-tools:
  - "Bash(mcp-coder gh-tool set-status *)"
---

# Approve Implementation Plan

Approve the implementation plan and transition the issue to implementation-ready state.

**Instructions:**
1. Run the set-status command to update the issue label:
```bash
mcp-coder gh-tool set-status status-05:plan-ready
```

2. Confirm the status change was successful.
**Note:** If the command fails, report the error to the user. Do not use `--force` unless explicitly asked.

**Effect:** Changes issue status from `status-04:plan-review` to `status-05:plan-ready`.
