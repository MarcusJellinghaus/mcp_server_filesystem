# Step 3: Clean Up `tach.toml` Subprocess Runner References

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 3: remove all `mcp_coder_utils.subprocess_runner` references from `tach.toml` since no production module uses subprocess anymore.

## WHERE

- **Modify**: `tach.toml`

## WHAT

Four removals:

1. Remove `{ path = "mcp_coder_utils.subprocess_runner" }` from `mcp_workspace.file_tools` depends_on
2. Remove `{ path = "mcp_coder_utils.subprocess_runner" }` from `mcp_workspace.git_operations` depends_on
3. Remove `{ path = "mcp_coder_utils.subprocess_runner" }` from `mcp_workspace.github_operations` depends_on
4. Remove the entire standalone `[[modules]]` block for `mcp_coder_utils.subprocess_runner`

## HOW

- Edit `tach.toml` directly — four deletions, no additions
- The standalone block to remove is:
  ```toml
  [[modules]]
  path = "mcp_coder_utils.subprocess_runner"
  layer = "utilities"
  depends_on = []
  ```

## DATA

- No code changes — configuration only
- No new dependencies introduced

## VERIFICATION

- pylint, mypy, pytest still pass (no code changed)
- `tach check` should pass if available

## COMMIT

`chore: remove stale subprocess_runner dependencies from tach.toml`
