# Step 3: Move github_operations Source Files from mcp_coder

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. This is step 3 of 5 for issue #104.
>
> **Task:** Copy all `github_operations` source files from the installed `mcp_coder` package into `src/mcp_workspace/github_operations/`. Adjust all imports per the remap table. Delete `update_workflow_label` from `manager.py`. Preserve `transition_issue_label`. Add `PyGithub` to `pyproject.toml` dependencies.
>
> **Source:** Use `get_library_source` MCP tool to read each file from the installed `mcp_coder.utils.github_operations` package. This is a copy+adjust-imports operation — no logic changes except the `update_workflow_label` deletion.

## WHERE

### New source files (16 total)

```
src/mcp_workspace/github_operations/
  __init__.py
  base_manager.py
  github_utils.py
  pr_manager.py
  labels_manager.py
  ci_results_manager.py
  issues/
    __init__.py
    base.py
    branch_manager.py
    branch_naming.py
    cache.py
    comments_mixin.py
    events_mixin.py
    labels_mixin.py
    manager.py
    types.py
```

### Files to modify

- `pyproject.toml` — add `PyGithub>=1.59.0` to `dependencies`

## WHAT

### Files to copy (read via `get_library_source`)

| Source (mcp_coder) | Destination (mcp_workspace) |
|----|-----|
| `mcp_coder.utils.github_operations.__init__` | `github_operations/__init__.py` |
| `mcp_coder.utils.github_operations.base_manager` | `github_operations/base_manager.py` |
| `mcp_coder.utils.github_operations.github_utils` | `github_operations/github_utils.py` |
| `mcp_coder.utils.github_operations.pr_manager` | `github_operations/pr_manager.py` |
| `mcp_coder.utils.github_operations.labels_manager` | `github_operations/labels_manager.py` |
| `mcp_coder.utils.github_operations.ci_results_manager` | `github_operations/ci_results_manager.py` |
| `mcp_coder.utils.github_operations.issues.__init__` | `github_operations/issues/__init__.py` |
| `mcp_coder.utils.github_operations.issues.base` | `github_operations/issues/base.py` |
| `mcp_coder.utils.github_operations.issues.branch_manager` | `github_operations/issues/branch_manager.py` |
| `mcp_coder.utils.github_operations.issues.branch_naming` | `github_operations/issues/branch_naming.py` |
| `mcp_coder.utils.github_operations.issues.cache` | `github_operations/issues/cache.py` |
| `mcp_coder.utils.github_operations.issues.comments_mixin` | `github_operations/issues/comments_mixin.py` |
| `mcp_coder.utils.github_operations.issues.events_mixin` | `github_operations/issues/events_mixin.py` |
| `mcp_coder.utils.github_operations.issues.labels_mixin` | `github_operations/issues/labels_mixin.py` |
| `mcp_coder.utils.github_operations.issues.manager` | `github_operations/issues/manager.py` |
| `mcp_coder.utils.github_operations.issues.types` | `github_operations/issues/types.py` |

## HOW

### Import remap (apply to every file after copying)

| Old import | New import |
|-----------|------------|
| `from mcp_coder.utils.log_utils import ...` | `from mcp_coder_utils.log_utils import ...` |
| `from mcp_coder.utils.subprocess_runner import ...` | `from mcp_coder_utils.subprocess_runner import ...` |
| `from mcp_coder.utils.git_operations.X import ...` | `from mcp_workspace.git_operations.X import ...` |
| `from mcp_coder.utils.user_config import get_config_values` | **REMOVE** (replaced by `config.get_github_token()` in base_manager) |
| `from mcp_coder.utils.github_operations.label_config import ...` | **REMOVE** (goes away with `update_workflow_label`) |
| `from ....constants import DUPLICATE_PROTECTION_SECONDS` | `from mcp_workspace.constants import DUPLICATE_PROTECTION_SECONDS` |
| `from ...timezone_utils import ...` | `from mcp_workspace.utils.timezone_utils import ...` |
| Relative imports within `github_operations` (e.g. `from .base_manager`) | Keep as-is (relative imports survive the move) |

### Specific changes to `base_manager.py`

Replace the `get_authenticated_username()` method's `user_config.get_config_values()` call:
```python
# OLD: token = user_config.get_config_values("github", "token")
# NEW: from mcp_workspace.config import get_github_token
#      token = get_github_token()
```

### Specific deletion in `manager.py`

Delete the entire `update_workflow_label` method from `IssueManager`. This method depends on `label_config.py` which stays in mcp_coder. Verify `transition_issue_label` is preserved (it's the generic primitive).

### pyproject.toml change

```toml
dependencies = [
    ...existing...,
    "PyGithub>=1.59.0",
]
```

### Pseudocode

```
for each source file in mcp_coder.utils.github_operations:
    content = get_library_source(file)
    content = apply_import_remap(content)
    save_file(destination_path, content)

edit(manager.py: delete update_workflow_label method)
edit(base_manager.py: replace user_config with config.get_github_token)
edit(pyproject.toml: add PyGithub)
```

## DATA

No new data structures. Existing classes and their public APIs are preserved as-is (except `update_workflow_label` removal).

### Key classes being moved

- `BaseGitHubManager(github_token: str)` — base class, takes explicit token param
- `PrManager` — PR creation/management
- `LabelsManager` — label CRUD operations
- `CiResultsManager` — CI status queries
- `IssueManager` — issue management with mixins (comments, events, labels, branches)

## Verification

```
pylint, mypy (expect some issues with missing test coverage — tests come in step 4)
Verify: no imports of mcp_coder.* in src/mcp_workspace/ (grep)
Verify: label_config.py, labels.json NOT present
Verify: update_workflow_label not present in manager.py
Verify: transition_issue_label IS present in manager.py (or labels_mixin.py)
```
