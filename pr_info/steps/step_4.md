# Step 4: Refactor `PullRequestManager` — repo_identifier replaces repository_url

> **Context**: See [summary.md](summary.md) for full issue context (#156: Support GHE URLs).

## Goal
Replace `self.repository_url: str` with `self.repo_identifier: RepoIdentifier` in `PullRequestManager`. Simplify `repository_name` property. Update all tests.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.
Implement Step 4: Refactor PullRequestManager to use repo_identifier.
Follow TDD — update tests first, then implement. Run all code quality checks after.
```

---

## WHERE

### Modified files
- `src/mcp_workspace/github_operations/pr_manager.py`
- `tests/github_operations/test_github_utils.py` (update PullRequestManager unit tests)
- `tests/github_operations/test_pr_manager.py` (update references)
- `tests/github_operations/test_pr_manager_find_by_head.py` (update if references repository_url)
- `tests/github_operations/test_pr_manager_closing_issues.py` (update if references repository_url)

## WHAT

### `pr_manager.py` — changes

**`__init__`**:
```python
def __init__(self, project_dir: Optional[Path] = None) -> None:
    super().__init__(project_dir)
    # self._repo_identifier is now a lazy property from BaseGitHubManager
    # Eagerly resolve it here to fail fast if no GitHub remote
    assert self.project_dir is not None
    try:
        _ = self._repo_identifier  # triggers resolution
    except ValueError as e:
        raise ValueError(
            f"Could not detect GitHub repository URL from git remote in: {self.project_dir}. "
            "Make sure the repository has a GitHub remote origin configured."
        ) from e
```

**Remove**: `self.repository_url` attribute assignment and `get_repository_identifier` import (no longer needed — `_repo_identifier` comes from `BaseGitHubManager`)

**`repository_name` property** — simplified:
```python
@property
def repository_name(self) -> str:
    try:
        return self._repo_identifier.full_name
    except Exception:
        return ""
```
Note: use `except Exception`, NOT `except (ValueError, Exception)` (the latter is redundant since `Exception` already covers `ValueError`).

**`find_pull_request_by_head`** — update owner extraction:
```python
# Before
owner = self.repository_name.split("/")[0]
# After
owner = self._repo_identifier.owner
```

### Import changes
```python
# Remove
from mcp_workspace.git_operations import get_repository_identifier
# (get_default_branch_name import stays)
```

## TESTS

### `tests/github_operations/test_pr_manager.py`

**Remove or rewrite `test_repository_url_property`** (~lines 188-201): This test asserts on `self.repository_url` which no longer exists. Either:
- Delete the test entirely, or
- Rewrite it to test `self._repo_identifier` instead (verify `.full_name`, `.hostname`, `.https_url`)

**Update other patches**: any mocking of `get_repository_identifier` → verify `_repo_identifier` is used directly from `BaseGitHubManager`.

### `tests/github_operations/test_github_utils.py` — `TestPullRequestManagerUnit`

**`test_direct_instantiation`** — update assertions:
```python
# Before
assert direct_manager.repository_url == "https://github.com/test/repo"
# After
assert direct_manager._repo_identifier.full_name == "test/repo"
assert direct_manager._repo_identifier.hostname == "github.com"
```

**`test_repository_name_property`** — no change needed (tests `repository_name` which still works)

### `test_pr_manager_find_by_head.py` — check if it references `repository_url`
- If yes, update to use `_repo_identifier`
- The `find_pull_request_by_head` method uses `self.repository_name` which is now backed by `_repo_identifier`

### `test_github_utils.py` — `TestPullRequestManagerIntegration`
- `test_pr_manager_lifecycle` — references `pr_manager.repository_url` in debug logging → update to `pr_manager._repo_identifier.https_url`
- `test_direct_instantiation` — update `repository_url` assertion
- `test_manager_properties` — no change (tests `repository_name` property)

## COMMIT
```
refactor: PullRequestManager uses repo_identifier instead of repository_url (#156)
```
