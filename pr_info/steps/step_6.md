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

`checks` must be on a **higher layer** than `github_operations` because `checks` imports from `github_operations` (e.g., `branch_status.py` imports `CIResultsManager`, `IssueManager`, `IssueData`). In import-linter, modules at the same layer (separated by `|`) **cannot** import each other.

`workflows` is at the same layer as `git_operations` (it has no dependencies on other tools-layer modules).

```ini
[importlinter:contract:layered_architecture]
layers =
    mcp_workspace.main
    mcp_workspace.server
    mcp_workspace.server_reference_tools
    mcp_workspace.checks
    mcp_workspace.file_tools | mcp_workspace.github_operations | mcp_workspace.reference_projects
    mcp_workspace.git_operations | mcp_workspace.workflows
    mcp_workspace.config | mcp_workspace.constants | mcp_workspace.utils
```

`checks` is on its own layer above `file_tools | github_operations | reference_projects` because it imports from `github_operations`. Modules on the same `|`-separated layer cannot import each other in import-linter. `workflows` stays at the `git_operations` layer since it has no upward deps.

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
    { path = "mcp_workspace.github_operations" },
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
