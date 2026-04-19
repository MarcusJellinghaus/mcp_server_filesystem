# Step 1: Git Primitives — `get_remote_url()` and `clone_repo()`

## LLM Prompt

> Implement Step 1 of Issue #92. See `pr_info/steps/summary.md` for full context.
> Add two git primitive functions to `remotes.py` following TDD. Tests first, then implementation.
> Run all code quality checks (pylint, pytest, mypy) after changes. Commit: `feat(git): add get_remote_url and clone_repo primitives`

## WHERE

- **Tests:** `tests/git_operations/test_remotes.py` (append new test class)
- **Implementation:** `src/mcp_workspace/git_operations/remotes.py` (add two functions)
- **Exports:** `src/mcp_workspace/git_operations/__init__.py` (add to imports and `__all__`)

## WHAT

### `get_remote_url(project_dir: Path) -> Optional[str]`

Returns the raw remote origin URL from any git repo. Unlike `get_github_repository_url()` which normalizes to GitHub HTTPS format, this returns the URL as-is (SSH, HTTPS, any host).

```
def get_remote_url(project_dir: Path) -> Optional[str]:
    if not is_git_repository(project_dir): return None
    open repo with _safe_repo_context
    if "origin" not in remotes: return None
    return repo.remotes.origin.url
```

**Returns:** Raw URL string, or `None` if not a git repo / no origin remote.

### `clone_repo(url: str, target_path: Path) -> None`

Full clone of a git repository. Wraps GitPython errors as `ValueError` with context.

```
def clone_repo(url: str, target_path: Path) -> None:
    validate url and target_path are non-empty
    if target_path exists: raise ValueError
    try: git.Repo.clone_from(url, str(target_path))
    except GitCommandError as e: raise ValueError(f"Failed to clone '{url}': {e}")
```

**Returns:** None. Raises `ValueError` on failure.

## HOW

- Import `git.Repo` (already available in the module's scope via `core.py` patterns)
- Use `_safe_repo_context` for `get_remote_url` (consistent with existing functions)
- Use `git.Repo.clone_from()` for `clone_repo` (GitPython's clone API)
- Follow existing error handling patterns in `remotes.py` (catch `InvalidGitRepositoryError`, `GitCommandError`)

## DATA

```python
# get_remote_url returns:
Optional[str]  # e.g. "git@github.com:org/repo.git" or "https://github.com/org/repo.git" or None

# clone_repo returns:
None  # raises ValueError on failure
```

## TESTS

Tests in `tests/git_operations/test_remotes.py` — add new test classes:

### `TestGetRemoteUrl`
- `test_returns_ssh_url` — repo with SSH remote → returns SSH URL as-is
- `test_returns_https_url` — repo with HTTPS remote → returns HTTPS URL as-is
- `test_returns_none_no_origin` — repo without origin → returns None
- `test_returns_none_not_git_repo` — plain directory → returns None

### `TestCloneRepo`
- `test_clone_success` — mock `Repo.clone_from`, verify called with correct args
- `test_clone_target_exists` — target dir exists → raises ValueError
- `test_clone_git_error` — mock `Repo.clone_from` raising error → raises ValueError with context
- `test_clone_empty_url` — empty URL → raises ValueError
- `test_clone_empty_target_path` — empty/None Path → raises ValueError

Mark clone tests that hit the filesystem with `@pytest.mark.git_integration` if they use real git operations; use mocks for unit tests.
