# Step 2: Add `.importlinter` Subprocess Ban Contract

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2: add a forbidden contract to `.importlinter` banning subprocess usage in production code. Run lint-imports to verify it passes.

## WHERE

- **Modify**: `.importlinter`

## WHAT

Add a new `forbidden` contract section banning:
- `subprocess` (stdlib)
- `mcp_coder_utils.subprocess_runner`
- `mcp_coder_utils.subprocess_streaming`

## HOW

Add to `.importlinter` following the existing contract pattern (e.g., `structlog_isolation`):

```ini
[importlinter:contract:subprocess_ban]
name = Subprocess Ban (use GitPython instead)
type = forbidden
source_modules =
    mcp_workspace
forbidden_modules =
    subprocess
    mcp_coder_utils.subprocess_runner
    mcp_coder_utils.subprocess_streaming
```

- `source_modules = mcp_workspace` means only production code is checked
- `tests/` is automatically exempt — it's not listed as a source module
- `tools/` is outside `root_packages` scope entirely, so also unaffected

## DATA

- No code changes — configuration only
- Depends on Step 1 being complete (otherwise `commits.py` would violate the ban)

## VERIFICATION

- Run `lint-imports` check to confirm the new contract passes
- pylint, mypy, pytest still pass (no code changed)

## COMMIT

`chore: add importlinter subprocess ban for production code`
