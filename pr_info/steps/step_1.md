# Step 1: Create `utils/repo_identifier.py` with hostname support

> **Context**: See [summary.md](summary.md) for full issue context (#156: Support GHE URLs).

## Goal
Create the foundation module `utils/repo_identifier.py` with `RepoIdentifier` (hostname-aware) and `hostname_to_api_base_url()`. Move existing tests, add GHE tests.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.
Implement Step 1: Create utils/repo_identifier.py with the enhanced RepoIdentifier dataclass.
Follow TDD — write tests first, then implement. Run all code quality checks after.
```

---

## WHERE

### New files
- `src/mcp_workspace/utils/repo_identifier.py`
- `tests/utils/__init__.py` (empty file — required for pytest to discover tests in this directory)
- `tests/utils/test_repo_identifier.py`

### Modified files
(none)

## WHAT

### `src/mcp_workspace/utils/repo_identifier.py`

```python
@dataclass
class RepoIdentifier:
    owner: str
    repo_name: str
    hostname: str = "github.com"

    @property
    def full_name(self) -> str: ...

    @property
    def cache_safe_name(self) -> str: ...

    @property
    def https_url(self) -> str: ...

    @property
    def api_base_url(self) -> str: ...

    def __str__(self) -> str: ...

    @classmethod
    def from_full_name(cls, full_name: str, hostname: str = "github.com") -> "RepoIdentifier": ...

    @classmethod
    def from_repo_url(cls, url: str) -> "RepoIdentifier": ...


def hostname_to_api_base_url(hostname: str) -> str: ...
```

## HOW

### `from_repo_url()` regex — generalized for any hostname
```
HTTPS pattern: https://[credentials@]<hostname>/<owner>/<repo>[.git][/]
SSH pattern:   git@<hostname>:<owner>/<repo>[.git][/]
```
- Credentials: `(?:[^@]+@)?` handles `token@`, `user:pass@`
- Hostname: `([^/]+)` captures any hostname (not just `github.com`)
- No short format `"owner/repo"` — use `from_full_name()` for that

### `hostname_to_api_base_url()` logic
```
if hostname == "github.com":
    return "https://api.github.com"
else:
    return f"https://{hostname}/api/v3"
```

### `api_base_url` property
```python
@property
def api_base_url(self) -> str:
    return hostname_to_api_base_url(self.hostname)
```

### `https_url` property
```python
@property
def https_url(self) -> str:
    return f"https://{self.hostname}/{self.owner}/{self.repo_name}"
```

## DATA

### RepoIdentifier fields
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `owner` | `str` | required | Repository owner/org |
| `repo_name` | `str` | required | Repository name |
| `hostname` | `str` | `"github.com"` | Git host (github.com or GHE hostname) |

### Properties
| Property | Returns | Example |
|----------|---------|---------|
| `full_name` | `"owner/repo"` | `"octocat/hello"` |
| `cache_safe_name` | `"owner_repo"` | `"octocat_hello"` |
| `https_url` | `"https://hostname/owner/repo"` | `"https://ghe.corp.com/org/app"` |
| `api_base_url` | API URL for PyGithub | `"https://ghe.corp.com/api/v3"` |

## TESTS — `tests/utils/test_repo_identifier.py`

### Existing behavior (moved from `tests/github_operations/test_repo_identifier.py`)
- `from_full_name()` — valid, no-slash, multi-slash, empty-owner, empty-repo
- `from_repo_url()` — HTTPS, HTTPS+.git, SSH, SSH+.git, invalid, non-string
- Properties — full_name, cache_safe_name, __str__

### New GHE tests
- `from_repo_url("https://ghe.corp.com/org/repo.git")` → hostname="ghe.corp.com"
- `from_repo_url("git@ghe.corp.com:org/repo.git")` → hostname="ghe.corp.com"
- `from_repo_url("https://token@ghe.corp.com/org/repo.git")` → credentials stripped
- `from_repo_url("https://user:pass@github.com/org/repo.git")` → credentials stripped
- `https_url` — github.com and GHE
- `api_base_url` — github.com returns `https://api.github.com`, GHE returns `https://host/api/v3`
- `hostname_to_api_base_url()` — standalone function tests
- `from_full_name("owner/repo", hostname="ghe.corp.com")` — custom hostname

## COMMIT
```
feat: create utils/repo_identifier.py with hostname support (#156)
```
