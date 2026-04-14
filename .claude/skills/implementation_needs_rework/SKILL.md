---
description: Return issue to plan-ready status for re-implementation after major review issues
disable-model-invocation: true
allowed-tools:
  - "Bash(mcp-coder gh-tool set-status *)"
---

# Return to plan-ready after major review issues

Transitions the issue back to `plan-ready` status for re-implementation when code review identifies major issues that cannot be fixed with minor changes.

## When to Use

| Situation | Action |
|-----------|--------|
| Minor fixes | Fix directly, re-run `/implementation_review` or `/implementation_review_supervisor` |
| **Major issues** | **This command** (after `/implementation_new_tasks` + `/commit_push`) |
| Approved | `/implementation_approve` |

## Prerequisites

- New implementation steps created (`/implementation_new_tasks`)
- Changes committed and pushed (`/commit_push`)

## Instructions

```bash
mcp-coder gh-tool set-status status-05:plan-ready
```

Confirm the status change was successful. If it fails, report the error. Do not use `--force` unless explicitly asked.

## Next Steps

Run `mcp-coder implement` to process the new steps, then `/implementation_review` or `/implementation_review_supervisor`.
