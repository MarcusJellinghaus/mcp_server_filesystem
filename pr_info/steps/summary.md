# Issue #156: Support GitHub Enterprise (GHE) URLs

## Problem
All GitHub URL parsing and PyGithub API initialization is hardcoded to `github.com`. Users on GitHub Enterprise instances get `WARNING: Could not get GitHub URL from repository`.

## Goal
Auto-detect hostname from git remote URLs and pass the correct `base_url` to PyGithub, so GHE users get full functionality without any configuration.

---

## Architectural / Design Changes

### Before
```
git_operations/remotes.py     → _parse_github_url()        hardcoded github.com
github_operations/github_utils.py → parse_github_url()     hardcoded github.com
                                  → format_github_https_url()  hardcoded github.com
                                  → get_repo_full_name()       hardcoded github.com
                                  → RepoIdentifier             no hostname field
github_operations/base_manager.py → Github()                no base_url param
                                  → _repo_owner/_repo_name   separate fields
```

### After
```
utils/repo_identifier.py      → RepoIdentifier              hostname field, any-host regex
                               → hostname_to_api_base_url()  github.com→api.github.com, GHE→host/api/v3
git_operations/remotes.py     → get_repository_identifier()  returns Optional[RepoIdentifier]
github_operations/base_manager.py → lazy _github_client      uses RepoIdentifier.api_base_url
                                  → lazy _repo_identifier     replaces _repo_owner/_repo_name/_repo_full_name
```

### Key Design Decisions
1. **RepoIdentifier moves to `utils/`** — both `git_operations/` and `github_operations/` need it; `utils/` is the shared leaf layer that both can import from (respects layer boundary).
2. **`hostname` field on RepoIdentifier** — auto-detected from the git remote URL, no config needed.
3. **Lazy `Github()` client** — hostname isn't known until `_repo_identifier` resolves (especially in `project_dir` mode), so client creation is deferred to first access.
4. **Unified `_repo_identifier`** — replaces `_repo_owner`, `_repo_name`, `_repo_full_name` with a single `RepoIdentifier` instance.
5. **Explicit `base_url` always** — even for `github.com`, pass `https://api.github.com` to `Github()`. No reliance on PyGithub defaults.

### Removed Functions (replaced by RepoIdentifier)
| Removed | Replacement |
|---------|-------------|
| `github_utils.parse_github_url()` | `RepoIdentifier.from_repo_url()` |
| `github_utils.format_github_https_url()` | `RepoIdentifier.https_url` |
| `github_utils.get_repo_full_name()` | `RepoIdentifier.full_name` |
| `remotes._parse_github_url()` | `RepoIdentifier.from_repo_url()` |

### Renamed Functions
| Before | After | Return Type Change |
|--------|-------|--------------------|
| `remotes.get_github_repository_url()` | `remotes.get_repository_identifier()` | `Optional[str]` → `Optional[RepoIdentifier]` |

---

## Files Created
| File | Purpose |
|------|---------|
| `src/mcp_workspace/utils/repo_identifier.py` | RepoIdentifier dataclass + hostname_to_api_base_url() |
| `tests/utils/__init__.py` | Empty file for pytest test discovery |
| `tests/utils/test_repo_identifier.py` | Tests for RepoIdentifier (moved + new GHE tests) |

## Files Modified
| File | Change |
|------|--------|
| `src/mcp_workspace/utils/__init__.py` | Empty → stays empty (no change needed) |
| `src/mcp_workspace/git_operations/remotes.py` | Delete `_parse_github_url()`, rename+retype `get_github_repository_url()` |
| `src/mcp_workspace/git_operations/__init__.py` | Export `get_repository_identifier` instead of `get_github_repository_url` |
| `src/mcp_workspace/github_operations/github_utils.py` | Remove RepoIdentifier, parse_github_url, format_github_https_url, get_repo_full_name |
| `src/mcp_workspace/github_operations/__init__.py` | Re-export RepoIdentifier from new location |
| `src/mcp_workspace/github_operations/base_manager.py` | Lazy _repo_identifier/_github_client, remove _repo_owner/_repo_name/_repo_full_name, hostname param on get_authenticated_username |
| `src/mcp_workspace/github_operations/pr_manager.py` | repo_identifier replaces repository_url, simplify repository_name |
| `tach.toml` | Add `mcp_workspace.utils` to git_operations depends_on |
| `tests/github_operations/test_repo_identifier.py` | Update import path, redirect to new location |
| `tests/github_operations/test_github_utils.py` | Remove tests for deleted functions |
| `tests/github_operations/test_base_manager.py` | Update for lazy init, GHE base_url |
| `tests/github_operations/test_pr_manager.py` | Update for repo_identifier replacing repository_url |
| `tests/git_operations/test_remotes.py` | Update for get_repository_identifier returning RepoIdentifier |
| `src/mcp_workspace/github_operations/issues/cache.py` | Update RepoIdentifier import to `utils.repo_identifier` |
| `tests/github_operations/test_issue_cache.py` | Update RepoIdentifier import to `utils.repo_identifier` |
| `tests/github_operations/test_ci_results_manager_foundation.py` | Update assertions for removed `_repo_owner`/`_repo_name`/`_repo_full_name` attributes |

## Implementation Steps Overview
1. **Create `utils/repo_identifier.py`** — RepoIdentifier with hostname support + tests
2. **Integrate RepoIdentifier** — delete old URL-parsing functions, rename `get_github_repository_url` → `get_repository_identifier`, update all callers/exports/tests across `git_operations/`, `github_operations/`, and `tach.toml`
3. **Refactor `BaseGitHubManager`** — lazy _repo_identifier/_github_client, get_authenticated_username hostname param + tests
4. **Refactor `PullRequestManager`** — repo_identifier replaces repository_url + tests
