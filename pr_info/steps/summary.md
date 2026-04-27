# Summary: Replace execute_command with GitPython and Ban Subprocess (#160)

## Goal

Remove the last subprocess usage in production code (`get_latest_commit_sha`) by replacing it with GitPython, then codify "no subprocess in production" as an architectural rule.

## Architectural / Design Changes

- **Subprocess elimination**: Production code (`src/mcp_workspace/`) will have zero subprocess dependencies. All git operations use GitPython natively.
- **New architectural rule**: `.importlinter` gains a `forbidden` contract banning `subprocess`, `mcp_coder_utils.subprocess_runner`, and `mcp_coder_utils.subprocess_streaming` from `mcp_workspace`. Tests are exempt.
- **Dependency cleanup**: `tach.toml` removes stale `subprocess_runner` declarations from modules that don't use it (and removes the standalone module entry).

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/git_operations/commits.py` | Replace `execute_command` with `safe_repo_context` |
| `.importlinter` | Add subprocess ban contract |
| `tach.toml` | Remove `subprocess_runner` from `file_tools`, `git_operations`, `github_operations` depends_on + remove standalone module entry |

## Steps

| Step | Description | Commit |
|------|-------------|--------|
| [Step 1](step_1.md) | Refactor `get_latest_commit_sha()` to use GitPython | `refactor: replace execute_command with GitPython in get_latest_commit_sha` |
| [Step 2](step_2.md) | Add `.importlinter` subprocess ban contract | `chore: add importlinter subprocess ban for production code` |
| [Step 3](step_3.md) | Clean up `tach.toml` subprocess_runner references | `chore: remove stale subprocess_runner dependencies from tach.toml` |
