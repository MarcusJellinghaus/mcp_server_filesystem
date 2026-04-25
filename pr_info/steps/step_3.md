# Step 3: Refactor `BaseGitHubManager` — lazy properties, unified RepoIdentifier

> **Context**: See [summary.md](summary.md) for full issue context (#156: Support GHE URLs).

## Goal
Refactor `BaseGitHubManager` to use lazy `_repo_identifier` and `_github_client` properties. Remove `_repo_owner`, `_repo_name`, `_repo_full_name`. Add `hostname` param to `get_authenticated_username()`. The `Github()` client is created lazily with the correct `base_url` from `RepoIdentifier.api_base_url`.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.
Implement Step 3: Refactor BaseGitHubManager with lazy properties and GHE support.
Follow TDD — update tests first, then implement. Run all code quality checks after.
```

---

## WHERE

### Modified files
- `src/mcp_workspace/github_operations/base_manager.py`
- `tests/github_operations/test_base_manager.py`
- `tests/github_operations/test_ci_results_manager_foundation.py`

## WHAT

### `base_manager.py` — new structure

```python
from mcp_workspace.utils.repo_identifier import RepoIdentifier, hostname_to_api_base_url

class BaseGitHubManager:
    def __init__(
        self,
        project_dir: Optional[Path] = None,
        repo_url: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> None:
        # Validate exactly one of project_dir/repo_url
        # Validate project_dir (exists, is_dir, is_git_repo) OR parse repo_url
        # Resolve and validate token (non-empty string)
        # Store: self.project_dir, self.github_token
        # Store: self._cached_repo_identifier (set for repo_url mode, None for project_dir mode)
        # DO NOT create Github() client here
        ...

    @property
    def _repo_identifier(self) -> RepoIdentifier:
        """Lazy property — resolves from git remote in project_dir mode."""
        ...

    @property  
    def _github_client(self) -> Github:
        """Lazy property — creates Github() with correct base_url."""
        ...

    def _get_repository(self) -> Optional[Repository]:
        """Get GitHub repo object using _repo_identifier.full_name."""
        ...


def get_authenticated_username(hostname: Optional[str] = None) -> str:
    """Get authenticated GitHub username.
    
    Args:
        hostname: GitHub hostname (default: "github.com"). For GHE, e.g. "ghe.corp.com".
    """
    ...
```

### Removed attributes
- `_repo_owner: Optional[str]`
- `_repo_name: Optional[str]`  
- `_repo_full_name: Optional[str]`
- `_github_client` as eagerly-created attribute (becomes lazy property)

### Removed methods
- `_init_with_repo_url()` — logic inlined in `__init__`
- `_init_with_project_dir()` — logic inlined in `__init__`

## ALGORITHM — `__init__`
```
validate exactly one of project_dir / repo_url
if project_dir: validate exists, is_dir, is_git_repo; store self.project_dir
if repo_url: parse with RepoIdentifier.from_repo_url(); store self._cached_repo_identifier
resolve token (explicit param or get_github_token()); validate non-empty string
store self.github_token; init self._cached_github_client = None, self._repository = None
```

## ALGORITHM — `_repo_identifier` property
```
if self._cached_repo_identifier is not None: return it
# project_dir mode — discover from git remote
identifier = git_operations.get_repository_identifier(self.project_dir)
if identifier is None: raise ValueError("Could not detect repository from git remote")
self._cached_repo_identifier = identifier
return identifier
```

## ALGORITHM — `_github_client` property
```
if self._cached_github_client is not None: return it
base_url = self._repo_identifier.api_base_url
self._cached_github_client = Github(auth=Auth.Token(self.github_token), base_url=base_url)
return self._cached_github_client
```

## ALGORITHM — `_get_repository()`
```
if self._repository is not None: return it (cached)
try:
    self._repository = self._github_client.get_repo(self._repo_identifier.full_name)
    return self._repository
except GithubException as e:
    log error using self._repo_identifier.https_url for context
    return None
```

## ALGORITHM — `get_authenticated_username(hostname)`
```
token = get_github_token()
validate token is string
base_url = hostname_to_api_base_url(hostname or "github.com")
client = Github(auth=Auth.Token(token), base_url=base_url)
return client.get_user().login
```

## DATA

### BaseGitHubManager instance attributes after refactor
| Attribute | Type | Set in |
|-----------|------|--------|
| `project_dir` | `Optional[Path]` | `__init__` |
| `github_token` | `str` | `__init__` |
| `_cached_repo_identifier` | `Optional[RepoIdentifier]` | `__init__` (repo_url mode) or `_repo_identifier` property |
| `_cached_github_client` | `Optional[Github]` | `_github_client` property |
| `_repository` | `Optional[Repository]` | `_get_repository()` |

## TESTS — `tests/github_operations/test_base_manager.py`

### Updated tests — `TestBaseGitHubManagerWithProjectDir`
- `test_successful_initialization_with_project_dir` — verify no `_repo_owner`/`_repo_name`/`_repo_full_name`, verify `_cached_github_client` is None (lazy), verify no `Github()` call in init
- `test_get_repository_with_project_dir_mode` — patch `get_repository_identifier` (was `get_github_repository_url`), verify `Github()` created with `base_url="https://api.github.com"`

### Updated tests — `TestBaseGitHubManagerWithRepoUrl`
- `test_successful_initialization_with_https_repo_url` — verify `_cached_repo_identifier` is set, no `Github()` call in init
- `test_successful_initialization_with_ssh_repo_url` — same
- `test_get_repository_with_repo_url_mode` — verify `Github()` created with correct `base_url`

### New GHE tests
- `test_ghe_repo_url_creates_client_with_ghe_base_url` — `repo_url="https://ghe.corp.com/org/repo"` → `Github(base_url="https://ghe.corp.com/api/v3")`
- `test_ghe_project_dir_creates_client_with_ghe_base_url` — mock `get_repository_identifier` returning GHE RepoIdentifier → verify `base_url`

### Updated tests — `get_authenticated_username`
- `test_get_authenticated_username_default_hostname` — verify `Github(base_url="https://api.github.com")`
- `test_get_authenticated_username_ghe_hostname` — verify `Github(base_url="https://ghe.corp.com/api/v3")`

### Updated tests — `tests/github_operations/test_ci_results_manager_foundation.py`

**Update assertions** that reference removed attributes `_repo_owner`, `_repo_name`, `_repo_full_name` (lines 52-54 and 191):
```python
# Before
assert manager._repo_owner == "test"
assert manager._repo_name == "repo"
assert manager._repo_full_name == "test/repo"
# After
assert manager._cached_repo_identifier.owner == "test"
assert manager._cached_repo_identifier.repo_name == "repo"
assert manager._cached_repo_identifier.full_name == "test/repo"
```

Apply the same pattern at line 191 (`_repo_full_name` → `_cached_repo_identifier.full_name`).

### `TestGithubTokenForwarding`
- Patch updates (`get_github_repository_url` → `get_repository_identifier`) already done in Step 2 — no changes needed here
- Remove assertions on `_repo_owner`, `_repo_name`, `_repo_full_name`

## COMMIT
```
refactor: BaseGitHubManager lazy client with GHE base_url support (#156)
```
