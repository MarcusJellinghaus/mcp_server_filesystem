---
allowed-tools: Bash(mcp-coder set-status:*)
workflow-stage: code-review
suggested-next: (bot runs create_pr) -> merge in GitHub
---

# Approve Implementation

Approve the implementation and transition the issue to PR-ready state.

**Instructions:**
1. Run the set-status command to update the issue label:
```bash
mcp-coder set-status status-08:ready-pr
```

2. Confirm the status change was successful.
**Note:** If the command fails, report the error to the user. Do not use `--force` unless explicitly asked.

**Effect:** Changes issue status from `status-07:code-review` to `status-08:ready-pr`.
