# Step 1: Config updates, architecture configs, and orphan cleanup

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. This is step 1 of 3 for issue #98.
>
> Update project configuration files to prepare for the git_operations package move.
> Register the `git_integration` pytest marker, update `.importlinter` and `tach.toml`
> for the new submodule structure, and delete the orphan test script.
> Run all checks (pylint, mypy, pytest) to confirm nothing breaks.

## WHERE

| File | Action |
|------|--------|
| `pyproject.toml` | Modify |
| `.importlinter` | Modify |
| `tach.toml` | Modify |
| `tests/integration_test_move.py` | Delete |

## WHAT

### 1. `pyproject.toml` — register `git_integration` marker

Add to `[tool.pytest.ini_options]`:

```toml
markers = [
    "git_integration: File system git operations (repos, commits)",
]
```

This is required because `--strict-markers` is active.

### 2. `.importlinter` — update GitPython isolation for submodules

Current ignore:
```
mcp_workspace.file_tools.git_operations -> git
```

When `git_operations` becomes a package, submodule imports like `mcp_workspace.file_tools.git_operations.core -> git` won't match. Update to:

```ini
ignore_imports =
    mcp_workspace.file_tools.git_operations.* -> git
```

**Verify**: Check import-linter docs — if wildcards aren't supported, list each submodule that imports `git` explicitly. At minimum: `core`, `file_tracking`, `staging`, `branches`, `commits`, `diffs`, `remotes`, `repository_status`. Read each source file at copy time (step 2) to determine the exact set.

**Alternative** (simpler, if wildcard works): A single wildcard line covers all submodules.

### 3. `tach.toml` — add subprocess_runner dependency

The incoming `commits.py` imports `mcp_coder_utils.subprocess_runner`. Add this to the `file_tools` module dependencies:

```toml
[[modules]]
path = "mcp_workspace.file_tools"
layer = "tools"
depends_on = [
    { path = "mcp_coder_utils.log_utils" },
    { path = "mcp_coder_utils.subprocess_runner" },
]
```

Also add the new module declaration:

```toml
[[modules]]
path = "mcp_coder_utils.subprocess_runner"
layer = "utilities"
depends_on = []
```

### 4. Delete orphan script

Delete `tests/integration_test_move.py`. It's not collected by pytest (filename mismatch — no `test_` prefix in the right sense), uses `print`-based assertions, and its coverage is provided by `tests/file_tools/test_move_operations.py` + `test_move_git_integration.py`.

## HOW

- Edit `pyproject.toml` to add markers list
- Edit `.importlinter` GitPython isolation contract
- Edit `tach.toml` to add dependency
- Delete the orphan file

## ALGORITHM

```
1. Add markers = ["git_integration: ..."] to pyproject.toml [tool.pytest.ini_options]
2. Update .importlinter gitpython_isolation ignore_imports to cover submodules
3. Add mcp_coder_utils.subprocess_runner to tach.toml file_tools depends_on
4. Delete tests/integration_test_move.py
5. Run pylint, mypy, pytest — all must pass
```

## DATA

No new data structures. Config-only changes.

## Commit message

```
chore: register git_integration marker, update arch configs, delete orphan script

- Register git_integration marker in pyproject.toml (--strict-markers)
- Update .importlinter GitPython isolation for git_operations submodules
- Add mcp_coder_utils.subprocess_runner to tach.toml file_tools deps
- Delete tests/integration_test_move.py (orphan, not pytest-collected)

Part of #98 — move git_operations into mcp_workspace (step 1/3)
```
