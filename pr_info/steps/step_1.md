# Step 1: Add `get_default_branch()` to `BaseGitHubManager`

**Ref:** See `pr_info/steps/summary.md` for full context (Issue #157).

## LLM Prompt

> Implement Step 1 of the verify_github plan (see `pr_info/steps/summary.md`).
> Add a `get_default_branch()` public method to `BaseGitHubManager` in `base_manager.py`, plus unit tests.
> Follow TDD: write tests first, then implement. Run all quality checks before committing.

## WHERE

| File | Action |
|------|--------|
| `tests/github_operations/test_base_manager.py` | Add `TestGetDefaultBranch` test class |
| `src/mcp_workspace/github_operations/base_manager.py` | Add `get_default_branch()` method |

## WHAT

```python
# base_manager.py — new method on BaseGitHubManager
def get_default_branch(self) -> str:
    """Get the default branch name from the GitHub repository.

    Returns:
        Default branch name (e.g., "main", "master", "develop")

    Raises:
        ValueError: If repository is not accessible
    """
```

## HOW

- Method calls `self._get_repository()` (existing, returns `Optional[Repository]`)
- If `None`, raises `ValueError`
- Returns `repo.default_branch` (PyGithub `Repository` attribute)
- No decorator needed — simple, no error swallowing

## ALGORITHM

```
repo = self._get_repository()
if repo is None:
    raise ValueError("Repository not accessible")
return repo.default_branch
```

## DATA

- **Input:** None (uses instance state)
- **Output:** `str` — branch name like `"main"`, `"master"`, `"develop"`
- **Errors:** `ValueError` if repo not accessible

## TESTS

Test class: `TestGetDefaultBranch` in `test_base_manager.py`

| Test | Setup | Assertion |
|------|-------|-----------|
| `test_get_default_branch_returns_main` | Mock repo with `default_branch = "main"` | Returns `"main"` |
| `test_get_default_branch_returns_master` | Mock repo with `default_branch = "master"` | Returns `"master"` |
| `test_get_default_branch_repo_not_accessible` | `_get_repository()` returns `None` | Raises `ValueError` |

Follow the existing test patterns in `TestBaseGitHubManagerWithRepoUrl` — use `repo_url` mode with patched `get_github_token` and `Github`.

## COMMIT

```
feat: add get_default_branch() to BaseGitHubManager (#157)
```
