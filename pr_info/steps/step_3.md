# Step 3: Remove old functions from `github_utils.py`

> **Context**: See [summary.md](summary.md) for full issue context (#156: Support GHE URLs).

## Goal
Remove `RepoIdentifier`, `parse_github_url()`, `format_github_https_url()`, and `get_repo_full_name()` from `github_utils.py`. Update `github_operations/__init__.py` to re-export `RepoIdentifier` from new location. Update all test imports.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.
Implement Step 3: Remove old functions from github_utils.py and update imports.
Follow TDD — update tests first, then implement. Run all code quality checks after.
```

---

## WHERE

### Modified files
- `src/mcp_workspace/github_operations/github_utils.py` — remove RepoIdentifier class, parse_github_url, format_github_https_url, get_repo_full_name (file may become empty or be deleted if nothing remains)
- `src/mcp_workspace/github_operations/__init__.py` — change RepoIdentifier import source
- `tests/github_operations/test_repo_identifier.py` — update imports to `mcp_workspace.utils.repo_identifier` (or redirect to new test file)
- `tests/github_operations/test_github_utils.py` — remove TestGitHubUtils class (tests for deleted functions), remove imports of deleted functions

## WHAT

### `github_utils.py` — after this step
The file becomes empty (or contains only the module docstring). All contents moved/replaced:
- `RepoIdentifier` → moved to `utils/repo_identifier.py` in Step 1
- `parse_github_url()` → replaced by `RepoIdentifier.from_repo_url()`
- `format_github_https_url()` → replaced by `RepoIdentifier.https_url`
- `get_repo_full_name()` → replaced by `RepoIdentifier.full_name`

### `__init__.py` — updated import
```python
# Before
from .github_utils import RepoIdentifier
# After
from mcp_workspace.utils.repo_identifier import RepoIdentifier
```

### `test_repo_identifier.py` — updated imports
```python
# Before
from mcp_workspace.github_operations.github_utils import RepoIdentifier
# After  
from mcp_workspace.utils.repo_identifier import RepoIdentifier
```
These tests should still pass as-is (RepoIdentifier API unchanged for existing tests).

### `test_github_utils.py` — removals
- Remove `from mcp_workspace.github_operations.github_utils import (format_github_https_url, get_repo_full_name, parse_github_url)`
- Remove entire `TestGitHubUtils` class
- Keep the rest of the file (fixtures, integration test classes for PullRequestManager, LabelsManager)

## HOW — finding all imports to update

Callers of removed functions that need updating (handled in this step or later steps):
- `base_manager.py` imports `parse_github_url` → updated in Step 4
- `pr_manager.py` imports `get_github_repository_url` (from git_operations) → updated in Step 5
- `pr_manager.py` uses `get_repo_full_name` via `repository_name` property → updated in Step 5
- `test_github_utils.py` imports all three → updated in this step
- `test_base_manager.py` patches `parse_github_url` → updated in Step 4

**Important**: Since `base_manager.py` and `pr_manager.py` still reference removed functions after this step, those imports must be updated in this step too (to keep the code importable), OR we update them here with temporary replacements. The cleanest approach: update `base_manager.py`'s import of `parse_github_url` in this step (replace with `RepoIdentifier.from_repo_url`), and update `pr_manager.py`'s import of `get_repo_full_name` in this step (inline the logic). The full refactor of those files happens in Steps 4 and 5.

### Minimal `base_manager.py` change in this step
```python
# Before
from .github_utils import parse_github_url
# After
from mcp_workspace.utils.repo_identifier import RepoIdentifier
```
And in `_init_with_repo_url()` and `_get_repository()`, replace `parse_github_url(url)` calls with:
```python
try:
    identifier = RepoIdentifier.from_repo_url(url)
    owner, repo_name = identifier.owner, identifier.repo_name
except ValueError:
    # handle error
```

### Minimal `pr_manager.py` change in this step
In `repository_name` property:
```python
# Before
from .github_utils import get_repo_full_name
repo_name = get_repo_full_name(self.repository_url)
# After
from mcp_workspace.utils.repo_identifier import RepoIdentifier
try:
    identifier = RepoIdentifier.from_repo_url(self.repository_url)
    return identifier.full_name
except ValueError:
    return ""
```

## TESTS

### Removed tests
- `TestGitHubUtils` class in `test_github_utils.py` (all methods test deleted functions)

### Updated tests  
- `test_repo_identifier.py` — import path change only, all tests pass unchanged
- `test_base_manager.py` — update patches: `parse_github_url` patches become `RepoIdentifier.from_repo_url` patches (or remove if not needed since from_repo_url is used inline)

## COMMIT
```
refactor: remove parse_github_url, format_github_https_url, get_repo_full_name (#156)
```
