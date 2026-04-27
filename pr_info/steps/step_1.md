# Step 1: Include hostname in cache_safe_name

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #158).

## Goal
Update `RepoIdentifier.cache_safe_name` to include the hostname, preventing cache file collisions between different GitHub hosts.

## Commit Message
`fix: include hostname in cache_safe_name to prevent cache collisions`

## WHERE
- `src/mcp_workspace/utils/repo_identifier.py` — `cache_safe_name` property (~line 58)
- `tests/github_operations/test_issue_cache.py` — `TestCacheFilePath` class (~lines 77-101)
- `tests/utils/test_repo_identifier.py` — `test_cache_safe_name_property` (~line 135)

## WHAT

### Property change
```python
@property
def cache_safe_name(self) -> str:
    """Return repository in 'hostname_owner_repo' format (safe for filenames)."""
    safe_hostname = self.hostname.replace(".", "_")
    return f"{safe_hostname}_{self.owner}_{self.repo_name}"
```

### Signature: unchanged — it's a property with no parameters

## HOW
- No new imports needed
- No integration point changes — `_get_cache_file_path()` already uses `repo_identifier.cache_safe_name`

## ALGORITHM
```
1. Take self.hostname (e.g., "github.com" or "ghe.corp.com")
2. Replace dots with underscores → "github_com" or "ghe_corp_com"
3. Return f"{safe_hostname}_{self.owner}_{self.repo_name}"
```

## DATA
- Input: `RepoIdentifier(owner="owner", repo_name="repo", hostname="github.com")`
- Output: `"github_com_owner_repo"` (was `"owner_repo"`)
- Input: `RepoIdentifier(owner="owner", repo_name="repo", hostname="ghe.corp.com")`
- Output: `"ghe_corp_com_owner_repo"`

## Test Changes

Update `TestCacheFilePath` assertions to expect the new format:

| Test | Old expected filename | New expected filename |
|------|----------------------|----------------------|
| `test_get_cache_file_path_basic` | `owner_repo.issues.json` | `github_com_owner_repo.issues.json` |
| `test_get_cache_file_path_complex_names` case 1 | `anthropics_claude-code.issues.json` | `github_com_anthropics_claude-code.issues.json` |
| `test_get_cache_file_path_complex_names` case 2 | `user_repo-with-dashes.issues.json` | `github_com_user_repo-with-dashes.issues.json` |
| `test_get_cache_file_path_complex_names` case 3 | `org_very.long.repo.name.issues.json` | `github_com_org_very.long.repo.name.issues.json` |

Update `test_cache_safe_name_property` in `tests/utils/test_repo_identifier.py`:

| Change | Old | New |
|--------|-----|-----|
| Assertion | `assert repo.cache_safe_name == "MarcusJellinghaus_mcp_coder"` | `assert repo.cache_safe_name == "github_com_MarcusJellinghaus_mcp_coder"` |
| Docstring | `"""Test cache_safe_name returns 'owner_repo' format."""` | `"""Test cache_safe_name returns 'hostname_owner_repo' format."""` |

Add new GHE-specific test case in `tests/utils/test_repo_identifier.py`:

```python
def test_cache_safe_name_with_ghe_hostname(self) -> None:
    """Test cache_safe_name includes non-default hostname."""
    repo = RepoIdentifier(owner="MarcusJellinghaus", repo_name="mcp_coder", hostname="ghe.corp.com")
    assert repo.cache_safe_name == "ghe_corp_com_MarcusJellinghaus_mcp_coder"
```

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

Implement Step 1 of Issue #158: Update the `cache_safe_name` property in
`src/mcp_workspace/utils/repo_identifier.py` to prepend the hostname
(dots replaced with underscores). Then update the `TestCacheFilePath` test
assertions in `tests/github_operations/test_issue_cache.py` to expect
the new filename format. Also update `test_cache_safe_name_property` in
`tests/utils/test_repo_identifier.py` to expect the new format, and add
a new `test_cache_safe_name_with_ghe_hostname` test case there.
Run all quality checks after.
```
