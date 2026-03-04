---
allowed-tools: Bash(mcp-coder set-status:*)
workflow-stage: plan-review
suggested-next: (bot runs implement) -> /clear -> implementation_review
---

# Approve Implementation Plan

Approve the implementation plan and transition the issue to implementation-ready state.

**Instructions:**
1. Run the set-status command to update the issue label:
```bash
mcp-coder set-status status-05:plan-ready
```

2. Confirm the status change was successful.

**Note:** If the command fails, report the error to the user. Do not use `--force` unless explicitly asked.

**Effect:** Changes issue status from `status-04:plan-review` to `status-05:plan-ready`.
