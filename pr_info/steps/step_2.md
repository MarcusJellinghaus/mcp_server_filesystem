# Step 2: Update `git_operations/remotes.py` — rename function, return RepoIdentifier

> **Context**: See [summary.md](summary.md) for full issue context (#156: Support GHE URLs).

## Goal
Replace `_parse_github_url()` and rename `get_github_repository_url()` → `get_repository_identifier()` returning `Optional[RepoIdentifier]`. Update all callers in `git_operations/`.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.
Implement Step 2: Update git_operations/remotes.py to use RepoIdentifier.
Follow TDD — update tests first, then implement. Run all code quality checks after.
```

---

## WHERE

### Modified files
- `src/mcp_workspace/git_operations/remotes.py`
- `src/mcp_workspace/git_operations/__init__.py`
- `tests/git_operations/test_remotes.py`

## WHAT

### `remotes.py` changes

**Delete**: `_parse_github_url()` function (entire function removed)

**Rename + retype**: `get_github_repository_url()` → `get_repository_identifier()`

```python
from mcp_workspace.utils.repo_identifier import RepoIdentifier

def get_repository_identifier(project_dir: Path) -> Optional[RepoIdentifier]:
    """Get repository identifier from git remote origin.
    
    Returns:
        RepoIdentifier if origin is a parseable git URL, None otherwise.
    """
```

**Remove**: `import re` (no longer needed — regex is in RepoIdentifier)

### `__init__.py` changes

Replace export:
```python
# Before
from mcp_workspace.git_operations.remotes import get_github_repository_url
# After
from mcp_workspace.git_operations.remotes import get_repository_identifier
```

Update `__all__` list accordingly.

## ALGORITHM — `get_repository_identifier()`
```
if not is_git_repository(project_dir): return None
repo = open_repo(project_dir)
if no "origin" remote: return None
origin_url = repo.remotes.origin.url
try:
    return RepoIdentifier.from_repo_url(origin_url)
except ValueError:
    return None
```

## TESTS — `tests/git_operations/test_remotes.py`

### Updated tests (rename + new return type)
- `test_get_repository_identifier` — HTTPS URL → returns RepoIdentifier with owner="user", repo_name="repo", hostname="github.com"
- `test_get_repository_identifier_with_ssh` — SSH URL → returns RepoIdentifier
- `test_get_repository_identifier_no_remote` — returns None
- `test_get_repository_identifier_ghe` — GHE HTTPS URL → returns RepoIdentifier with hostname="ghe.corp.com"

### Existing tests unchanged
- `TestGitPushForceWithLease` — no changes needed
- `TestRebaseOntoBranch` — no changes needed
- `TestGetRemoteUrl` — no changes needed
- `TestCloneRepo` — no changes needed

## COMMIT
```
refactor: rename get_github_repository_url to get_repository_identifier (#156)
```
