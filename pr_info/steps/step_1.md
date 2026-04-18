# Step 1: Fix wrong package references in claude_local.bat

**Depends on:** nothing
**Commit message:** `fix(claude_local.bat): reference mcp-workspace instead of mcp-coder (#80)`

## Context

See [summary.md](summary.md) for full context. `claude_local.bat` Step 4 checks whether the package is editable-installed, but references `mcp-coder` instead of `mcp-workspace` in three places.

## WHERE

- `claude_local.bat` (project root)

## WHAT

Three text replacements, no signature or function changes:

| Line | Old | New |
|------|-----|-----|
| 6 | `Assumes mcp-coder is editable-installed` | `Assumes mcp-workspace is editable-installed` |
| 69 | `pip show mcp-coder` | `pip show mcp-workspace` |
| 82 | `mcp-coder does not appear` | `mcp-workspace does not appear` |

## HOW

Use `edit_file` with three exact-match edits on `claude_local.bat`.

## ALGORITHM

```
1. Replace "mcp-coder" with "mcp-workspace" in line 6 comment
2. Replace "mcp-coder" with "mcp-workspace" in line 69 pip show command
3. Replace "mcp-coder" with "mcp-workspace" in line 82 warning message
4. Run pylint, pytest, mypy checks (all must pass)
5. Commit
```

## DATA

No return values or data structures — batch file text only.

## TESTS

Not applicable — no Python test suite covers batch file content. Verified by code review and running `claude_local.bat`.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. In `claude_local.bat`, replace the three occurrences of `mcp-coder` with `mcp-workspace` on lines 6, 69, and 82 as specified. Run code quality checks afterward. Commit with message: `fix(claude_local.bat): reference mcp-workspace instead of mcp-coder (#80)`
