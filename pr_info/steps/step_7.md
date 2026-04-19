# Step 7: Config Files — Architecture Enforcement + `.mcp.json` Migration

## LLM Prompt

> Implement Step 7 of Issue #92. See `pr_info/steps/summary.md` for full context.
> Update architecture config files to include the new `reference_projects` module and migrate `.mcp.json` to the new KV format.
> Run all code quality checks (pylint, pytest, mypy) after changes. Commit: `chore(config): add reference_projects to architecture configs, migrate .mcp.json`

## WHERE

- `.importlinter` — add `reference_projects` to layered architecture
- `tach.toml` — add `reference_projects` module block
- `vulture_whitelist.py` — add `search_reference_files` entry
- `.mcp.json` — migrate 4 reference projects to new KV format

## WHAT

### `.importlinter` — layered architecture update

Add `mcp_workspace.reference_projects` at the tools layer:

```ini
layers =
    mcp_workspace.main
    mcp_workspace.server
    mcp_workspace.file_tools | mcp_workspace.github_operations | mcp_workspace.reference_projects
    mcp_workspace.git_operations
    mcp_workspace.config | mcp_workspace.constants | mcp_workspace.utils
```

### `tach.toml` — new module block

```toml
[[modules]]
path = "mcp_workspace.reference_projects"
layer = "tools"
depends_on = [
    { path = "mcp_workspace.git_operations" },
]
```

Also add `{ path = "mcp_workspace.reference_projects" }` to `mcp_workspace.server`'s `depends_on` and to `mcp_workspace.main`'s `depends_on`.

### `vulture_whitelist.py` — new tool entry

```python
# Under "# Reference project tools"
_.search_reference_files
```

### `.mcp.json` — migrate to KV format

```
# Before:
"p_coder=${USERPROFILE}\\Documents\\GitHub\\mcp_coder"

# After:
"name=p_coder,path=${USERPROFILE}\\Documents\\GitHub\\mcp_coder"
```

Apply to all 4 reference project entries.

## HOW

- These are all config-only changes — no code logic
- `.importlinter` change ensures `reference_projects.py` is recognized at the correct architectural layer
- `tach.toml` change enables boundary enforcement for the new module
- `vulture_whitelist.py` prevents false positive for dynamically-registered MCP tool
- `.mcp.json` migration is required for the new KV parser (Step 4)

## VERIFICATION

After changes, verify:
1. `lint-imports` passes (import linter)
2. `tach check` passes (boundary enforcement)
3. `vulture` passes (no false unused code reports)
4. All existing quality checks still pass (pylint, pytest, mypy)
