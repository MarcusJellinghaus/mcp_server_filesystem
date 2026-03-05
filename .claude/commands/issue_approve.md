---
allowed-tools: Bash(gh issue comment:*), Read, Bash(MSYS_NO_PATHCONV=1 gh issue comment:*)
workflow-stage: issue-discussion
suggested-next: (bot runs create_plan) -> /clear -> plan_review
---

# Approve Issue

Approve the current issue to transition it to the next status in the workflow.

**Instructions:**

1. If no issue context is found from prior `/issue_analyse` or `/issue_create`, respond: "No issue context found. Please run `/issue_analyse <number>` or `/issue_create` first."

2. Validate that the issue is ready for approval:
   - Issue has been analyzed/discussed
   - Requirements are clear
   - No blocking questions remain

3. Comment `/approve` on the issue (use MSYS_NO_PATHCONV to prevent Windows Git Bash path conversion):

```bash
MSYS_NO_PATHCONV=1 gh issue comment <issue_number> --body "/approve"
```

This triggers the GitHub Action to promote the issue status (e.g., `status-01:created` → `status-02:awaiting-planning`).
