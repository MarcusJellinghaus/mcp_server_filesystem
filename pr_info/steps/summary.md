# Issue #82: Add `[tool.mcp-coder.from-github]` config to pyproject.toml

## Summary

Add a `[tool.mcp-coder.from-github]` section to `pyproject.toml` so that `mcp-coder vscodeclaude launch --from-github` knows which packages to override from GitHub for this project.

## Architectural / Design Changes

**None.** This is a config-only change — no source code, no new modules, no behavioral changes. The new TOML section is read by the external `mcp-coder` tool (not by this project's code) to determine which packages to install from GitHub when launching with the `--from-github` flag.

The config distinguishes two install strategies:
- **`packages`** (with deps): Leaf packages that may pull in new external dependencies (e.g., `mcp-config-tool`).
- **`packages-no-deps`** (without deps): Sibling packages installed without dependencies to avoid downgrading each other (e.g., `mcp-tools-py`, `mcp-coder`).

## Files Modified

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | **Modified** | Insert `[tool.mcp-coder.from-github]` section between `[tool.isort]` and `[tool.pylint.messages_control]` |

No files created. No files deleted.

## Implementation Steps

| Step | Description |
|------|-------------|
| [Step 1](step_1.md) | Add `[tool.mcp-coder.from-github]` config block to `pyproject.toml` |
