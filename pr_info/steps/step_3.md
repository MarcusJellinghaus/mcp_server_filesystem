# Step 3: Final verification and stale reference cleanup

## Summary

See [summary.md](summary.md) for full context.

Grep for any remaining `mcp_workspace.log_utils` references and run full checks.

## WHERE

All files in the repo (read-only scan), no edits expected unless stale references found.

## WHAT

1. Grep the entire repo for `mcp_workspace.log_utils` — should return zero matches
2. Grep for `mcp_workspace/log_utils` (path form) — should return zero matches
3. Run pylint, pytest, mypy — all must pass

## HOW

1. Search for stale references
2. Fix any found (not expected if steps 1-2 were done correctly)
3. Run all three checks
4. Confirm clean

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement step 3: grep the entire repo for any remaining references to
mcp_workspace.log_utils or mcp_workspace/log_utils. Fix any found. Run
pylint, pytest (excluding integration markers), and mypy. Confirm all clean.
```
