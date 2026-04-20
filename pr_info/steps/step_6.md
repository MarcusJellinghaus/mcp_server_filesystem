# Step 6: Update architecture configs for new modules

> See [summary.md](./summary.md) for full context. This is step 6 of 6.

## Goal

Update `.importlinter`, `tach.toml`, and `vulture_whitelist.py` to register the new packages and MCP tools. This is done as a final step so all source modules exist and checks can be validated end-to-end.

Note: `vulture_whitelist.py` entries for individual tools may have been added in steps 3-5 alongside the tool. This step ensures all three are present and adds the architecture boundary configs.

## LLM Prompt

```
Implement step 6 from pr_info/steps/step_6.md. Read pr_info/steps/summary.md for context.
Update .importlinter, tach.toml, and vulture_whitelist.py for the new checks/ and
workflows/ packages. Ensure all architecture checks pass (import-linter, tach, vulture).
Run all code quality checks (pylint, pytest, mypy).
```

## WHERE

| Action | Path |
|--------|------|
| Modify | `.importlinter` |
| Modify | `tach.toml` |
| Modify | `vulture_whitelist.py` (verify all 3 tool names present) |

## WHAT — `.importlinter` changes

Add `mcp_workspace.checks` and `mcp_workspace.workflows` to the layered architecture contract.

`checks` is at the same layer as `file_tools | github_operations` because it depends on both `git_operations` and `github_operations`.

`workflows` is at the same layer as `git_operations` (it has no dependencies on other tools-layer modules).

```ini
[importlinter:contract:layered_architecture]
layers =
    mcp_workspace.main
    mcp_workspace.server
    mcp_workspace.server_reference_tools
    mcp_workspace.file_tools | mcp_workspace.github_operations | mcp_workspace.reference_projects | mcp_workspace.checks
    mcp_workspace.git_operations | mcp_workspace.workflows
    mcp_workspace.config | mcp_workspace.constants | mcp_workspace.utils
```

Note: `checks` depends on `github_operations` (same layer via `|`) and on `workflows` + `git_operations` (lower layer). The `|` means "same layer, may import each other". Since `checks` needs `github_operations`, they share a layer. `workflows` drops to `git_operations` layer since it has no upward deps.

**Important**: If `checks` does NOT import `github_operations` at the Python level but only uses it at runtime, it can stay on the same layer. Review actual imports in the moved code to confirm layer placement.

## WHAT — `tach.toml` changes

Add two new module entries and update `server` dependencies:

```toml
# Add to server depends_on:
[[modules]]
path = "mcp_workspace.server"
layer = "protocol"
depends_on = [
    { path = "mcp_workspace.file_tools" },
    { path = "mcp_workspace.git_operations" },
    { path = "mcp_workspace.checks" },
    { path = "mcp_workspace.reference_projects" },
    { path = "mcp_workspace.server_reference_tools" },
    { path = "mcp_coder_utils.log_utils" },
]

# New module: checks
[[modules]]
path = "mcp_workspace.checks"
layer = "tools"
depends_on = [
    { path = "mcp_workspace.git_operations" },
    { path = "mcp_workspace.github_operations" },
    { path = "mcp_workspace.workflows" },
    { path = "mcp_workspace.file_tools" },
]

# New module: workflows
[[modules]]
path = "mcp_workspace.workflows"
layer = "tools"
depends_on = []

# Update tests to include new modules:
[[modules]]
path = "tests"
depends_on = [
    # ... existing deps ...
    { path = "mcp_workspace.checks" },
    { path = "mcp_workspace.workflows" },
]
```

## WHAT — `vulture_whitelist.py` changes

Ensure these three tool handler names are present (some may already be added in steps 3-5):

```python
# New MCP tools for checks (#114)
_.check_branch_status
_.check_file_size
_.get_base_branch
```

## HOW — Verification

After making changes, verify:
1. `pylint` passes
2. `pytest` passes
3. `mypy` passes
4. Import-linter contracts pass (if available locally)
5. Tach boundaries pass (if available locally)

## Commit

```
chore: update architecture configs for new modules

Add checks/ and workflows/ packages to .importlinter layered
architecture and tach.toml module boundaries. Ensure vulture
whitelist includes all new MCP tool handlers.

Ref: #114
```
