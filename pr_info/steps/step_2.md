# Step 2: Integrate RepoIdentifier — delete old functions, rename, update all callers

> **Context**: See [summary.md](summary.md) for full issue context (#156: Support GHE URLs).

## Goal
Atomic step: delete all old URL-parsing functions, rename `get_github_repository_url` → `get_repository_identifier`, update all exports/imports/callers/tests across the codebase. After this step, `RepoIdentifier` (from `utils/`) is the single source of truth for repository identity.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.
Implement Step 2: Integrate RepoIdentifier across the codebase — delete old functions, rename, update all callers.
Follow TDD — update tests first, then implement. Run all code quality checks after.
```

---

## WHERE

### Modified files — `git_operations/`
- `src/mcp_workspace/git_operations/remotes.py`
- `src/mcp_workspace/git_operations/__init__.py`

### Modified files — `github_operations/`
- `src/mcp_workspace/github_operations/github_utils.py`
- `src/mcp_workspace/github_operations/__init__.py`
- `src/mcp_workspace/github_operations/base_manager.py`
- `src/mcp_workspace/github_operations/pr_manager.py`
- `src/mcp_workspace/github_operations/issues/cache.py`

### Modified files — config
- `tach.toml` — add `mcp_workspace.utils` to `git_operations.depends_on`

### Modified test files
- `tests/git_operations/test_remotes.py`
- `tests/github_operations/test_github_utils.py`
- `tests/github_operations/test_base_manager.py`
- `tests/github_operations/test_pr_manager.py`
- `tests/github_operations/test_repo_identifier.py`
- `tests/github_operations/test_issue_cache.py`

---

## WHAT — detailed per file

### 1. `src/mcp_workspace/git_operations/remotes.py`

**Delete**: `_parse_github_url()` function (entire function, ~lines 281+)

**Delete**: `import re` (no longer needed — regex lives in `RepoIdentifier`)

**Add import**: `from mcp_workspace.utils.repo_identifier import RepoIdentifier`

**Rename + retype**: `get_github_repository_url()` → `get_repository_identifier()`
- Old signature: `def get_github_repository_url(project_dir: Path) -> Optional[str]`
- New signature: `def get_repository_identifier(project_dir: Path) -> Optional[RepoIdentifier]`
- New docstring: `"""Get repository identifier from git remote origin. Returns RepoIdentifier if origin is a parseable git URL, None otherwise."""`
- Implementation: use `RepoIdentifier.from_repo_url(origin_url)` instead of `_parse_github_url()`; catch `ValueError` → return `None`

**Update docstring**: `get_remote_url()` docstring (line 18) references `get_github_repository_url` — change to `get_repository_identifier`

### 2. `src/mcp_workspace/git_operations/__init__.py`

**Replace import**:
```python
# Before
from mcp_workspace.git_operations.remotes import get_github_repository_url
# After
from mcp_workspace.git_operations.remotes import get_repository_identifier
```

**Update `__all__`**: replace `"get_github_repository_url"` with `"get_repository_identifier"`

### 3. `src/mcp_workspace/github_operations/github_utils.py`

**Delete** these functions/classes (the entire definitions):
- `parse_github_url()` (~line 115)
- `format_github_https_url()` (~line 163)
- `get_repo_full_name()` (~line 180)

**Delete**: The `RepoIdentifier` class (moved to `utils/repo_identifier.py` in Step 1)

After removing all four definitions, delete `github_utils.py` entirely — no stub file needed. The now-unused imports (`re`, `dataclass`, `Optional`, `Tuple`) go with it.

### 4. `src/mcp_workspace/github_operations/__init__.py`

**Change RepoIdentifier import source**:
```python
# Before
from .github_utils import RepoIdentifier
# After
from mcp_workspace.utils.repo_identifier import RepoIdentifier
```

**Remove** any exports for deleted functions (`parse_github_url`, `format_github_https_url`, `get_repo_full_name`) — check if they are in `__all__`.

### 5. `src/mcp_workspace/github_operations/base_manager.py`

**Replace import**:
```python
# Before
from .github_utils import parse_github_url
# After
from mcp_workspace.utils.repo_identifier import RepoIdentifier
```

**Update `_init_with_repo_url()`** (~line 224):
```python
# Before
parsed = parse_github_url(repo_url)
if parsed:
    owner, repo_name = parsed
    ...
# After
try:
    identifier = RepoIdentifier.from_repo_url(repo_url)
    owner, repo_name = identifier.owner, identifier.repo_name
    ...
except ValueError:
    # handle error (same as the old `if not parsed` branch)
```

**Update `_init_with_project_dir()`** (~lines 263-267):
```python
# Before
github_url = git_operations.get_github_repository_url(self.project_dir)
...
parsed = parse_github_url(github_url)
# After
identifier = git_operations.get_repository_identifier(self.project_dir)
# Use identifier.owner, identifier.repo_name directly (no second parse)
```
Refactor so the `get_repository_identifier` result is used directly — no need to call `parse_github_url` on an already-parsed URL.

### 6. `src/mcp_workspace/github_operations/pr_manager.py`

**Replace import**:
```python
# Before
from mcp_workspace.git_operations import get_github_repository_url
# After
from mcp_workspace.git_operations import get_repository_identifier
```

**Update `__init__`** (~line 76):
```python
# Before
self.repository_url = get_github_repository_url(self.project_dir)
# After
repo_id = get_repository_identifier(self.project_dir)
self.repository_url = repo_id.https_url if repo_id else None
```
(Keep `self.repository_url` as a string for now — full replacement to `repo_identifier` happens in Step 4.)

**Update `repository_name` property** (~line 504-510):
```python
# Before
from .github_utils import get_repo_full_name
...
repo_name = get_repo_full_name(self.repository_url)
# After
from mcp_workspace.utils.repo_identifier import RepoIdentifier
try:
    identifier = RepoIdentifier.from_repo_url(self.repository_url)
    return identifier.full_name
except (ValueError, TypeError):
    return ""
```

### 7. `src/mcp_workspace/github_operations/issues/cache.py`

**Replace import** (line 35):
```python
# Before
from ..github_utils import RepoIdentifier
# After
from mcp_workspace.utils.repo_identifier import RepoIdentifier
```

### 8. `tach.toml`

Add `{ path = "mcp_workspace.utils" }` to the `depends_on` list for `[[modules]]` entry with `path = "mcp_workspace.git_operations"`. This is needed because `git_operations/remotes.py` now imports from `utils/repo_identifier.py`.

---

## TESTS — detailed per file

### `tests/git_operations/test_remotes.py`

**Rename all test functions/references**:
- `test_get_github_repository_url*` → `test_get_repository_identifier*`
- Update mock patches: `get_github_repository_url` → `get_repository_identifier`
- Update assertions: old tests checked for a URL string, new tests check for `RepoIdentifier` attributes (`.owner`, `.repo_name`, `.hostname`)
- Old: `assert result == "https://github.com/user/repo"`
- New: `assert result.owner == "user"` / `assert result.repo_name == "repo"` / `assert result.hostname == "github.com"`

**Add new test**:
- `test_get_repository_identifier_ghe` — GHE HTTPS URL → returns RepoIdentifier with `hostname="ghe.corp.com"`

### `tests/github_operations/test_github_utils.py`

**Remove imports**: `parse_github_url`, `format_github_https_url`, `get_repo_full_name`

**Remove**: `TestGitHubUtils` class entirely (all methods test deleted functions)

**Keep**: all other test classes (fixtures, `TestPullRequestManagerUnit`, `TestPullRequestManagerIntegration`, `TestLabelsManagerUnit`, etc.)

**Update `TestPullRequestManagerUnit`** and **`TestPullRequestManagerIntegration`**: any references to `get_github_repository_url` in mock patches must be updated to `get_repository_identifier`, and mock return values must change from URL strings to `RepoIdentifier` instances.

### `tests/github_operations/test_base_manager.py`

**Update all patches** of `get_github_repository_url` → `get_repository_identifier`:
- Lines ~353, 652, 692, 721, 750, 787, 824, 864: change patch target from `...git_operations.get_github_repository_url` to `...git_operations.get_repository_identifier`
- Change mock return values from URL strings to `RepoIdentifier(owner="...", repo_name="...")`

**Update all patches** of `parse_github_url`:
- Change from patching `parse_github_url` to patching `RepoIdentifier.from_repo_url` (or inline the behavior)
- Update return values from `("owner", "repo")` tuples to `RepoIdentifier` instances

**Line ~974**: patch target `mcp_workspace.github_operations.pr_manager.get_github_repository_url` → `mcp_workspace.github_operations.pr_manager.get_repository_identifier`

### `tests/github_operations/test_pr_manager.py`

**Update patches**: any mocking of `get_github_repository_url` → `get_repository_identifier` with `RepoIdentifier` return values.

### `tests/github_operations/test_repo_identifier.py`

**Update imports**:
```python
# Before
from mcp_workspace.github_operations.github_utils import RepoIdentifier
# After
from mcp_workspace.utils.repo_identifier import RepoIdentifier
```

All test logic should remain unchanged — the `RepoIdentifier` API is the same. If this file substantially duplicates the new `tests/utils/test_repo_identifier.py` from Step 1, delete it and redirect. Otherwise, update the import path only.

### `tests/github_operations/test_issue_cache.py`

**Update import** (line 17):
```python
# Before
from mcp_workspace.github_operations.github_utils import RepoIdentifier
# After
from mcp_workspace.utils.repo_identifier import RepoIdentifier
```

All test logic should remain unchanged — only the import path changes.

---

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

---

## HOW — implementation order

1. Update `tach.toml` first (architecture dependency)
2. Update `remotes.py` (delete `_parse_github_url`, rename function, update docstrings)
3. Update `git_operations/__init__.py` (export rename)
4. Update `github_operations/__init__.py` (re-export source)
5. Delete `github_utils.py`
6. Update `base_manager.py` (replace `parse_github_url` usage with `RepoIdentifier`)
7. Update `pr_manager.py` (replace `get_github_repository_url` usage, replace `get_repo_full_name` usage)
8. Update all test files in one pass
9. Run `pylint`, `pytest`, `mypy` — all must pass

## COMMIT
```
refactor: integrate RepoIdentifier, delete old URL-parsing functions (#156)
```
