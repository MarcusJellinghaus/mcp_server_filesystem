# Issue #80: fix(claude_local.bat): editable-install check references wrong package

## Summary

`claude_local.bat` references `mcp-coder` in three places where it should reference `mcp-workspace`. This is a text-only fix — no logic, architecture, or design changes.

## Architectural / Design Changes

None. This is a cosmetic/correctness fix to a batch script. No code paths, data structures, or integrations change.

## Files Modified

| File | Change |
|------|--------|
| `claude_local.bat` | Fix 3 occurrences of `mcp-coder` → `mcp-workspace` (lines 6, 69, 82) |

## Files Created

| File | Purpose |
|------|---------|
| `pr_info/steps/summary.md` | This summary |
| `pr_info/steps/step_1.md` | Single implementation step |

## Test-Driven Development

Not applicable — this is a batch file with no corresponding test suite. The fix is verified by visual inspection and running the script.

## Steps Overview

| Step | Description |
|------|-------------|
| 1 | Fix all three wrong-package references in `claude_local.bat` |
