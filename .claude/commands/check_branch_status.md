---
allowed-tools: Bash(mcp-coder check branch-status:*)
workflow-stage: quality-check
suggested-next: commit_push, rebase
---

# Check Branch Status

Check comprehensive branch readiness including CI status, rebase requirements, task completion, and GitHub labels.

## Usage

Call the underlying CLI command with LLM-optimized output and CI waiting:

```bash
mcp-coder check branch-status --ci-timeout 180 --llm-truncate
```

## What This Command Does

1. **CI Status Check**: Analyzes latest workflow run and retrieves error logs
2. **Rebase Detection**: Checks if branch needs rebasing onto main
3. **Task Validation**: Verifies all implementation tasks are complete
4. **GitHub Labels**: Reports current workflow status label
5. **Recommendations**: Provides actionable next steps

## Follow-Up Actions

Based on the status report, use these commands for next steps:

| Status | Action |
|--------|--------|
| CI failures | Fix the issues shown in the CI error details |
| Rebase needed | Run `/rebase` to rebase onto base branch with conflict resolution |
| Tasks incomplete | Complete remaining tasks manually |
| CI green + tasks done | Run `/commit_push` to commit and push changes |
| Ready to merge | Create PR or merge via GitHub |

## Output Format

LLM-optimized output with:
- CI error logs for failed jobs (truncated to ~300 lines total)
- Complete status information for all other components
- Clear status indicators
- Actionable recommendations

## Integration

This slash command enables interactive workflow management:
- Check readiness before creating PRs
- Diagnose CI failures
- Validate task completion
- Identify when rebase is needed (then use `/rebase`)

## Rationale

**Rationale**: LLM-driven context benefits from waiting for complete results. The 180-second timeout provides a balance between responsiveness and allowing typical CI runs to complete. No `--fix` by default to let LLM analyze failures and suggest targeted fixes.
