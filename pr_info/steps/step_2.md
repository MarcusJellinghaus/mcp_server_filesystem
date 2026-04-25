# Step 2: Add `CheckResult` TypedDict + `verify_github()` with connectivity checks (1–4)

**Ref:** See `pr_info/steps/summary.md` for full context (Issue #157).

## LLM Prompt

> Implement Step 2 of the verify_github plan (see `pr_info/steps/summary.md`).
> Create `verification.py` with `CheckResult` TypedDict and `verify_github()` function implementing checks 1–4 (token, auth, repo URL, repo access).
> Branch protection checks (5–9) will be added in Step 3.
> Follow TDD: write tests first in `test_verification.py`, then implement. Run all quality checks before committing.

## WHERE

| File | Action |
|------|--------|
| `tests/github_operations/test_verification.py` | **Create** — unit tests for checks 1–4 |
| `src/mcp_workspace/github_operations/verification.py` | **Create** — `CheckResult` + `verify_github()` |

## WHAT

```python
# verification.py

from typing import Literal, NotRequired, TypedDict

class CheckResult(TypedDict):
    ok: bool
    value: str
    severity: Literal["error", "warning"]
    error: NotRequired[str]
    install_hint: NotRequired[str]

def verify_github(project_dir: Path) -> dict[str, object]:
    """Verify GitHub connectivity and branch protection.

    Returns dict with 'overall_ok' bool and per-check CheckResult entries.
    """
```

## HOW

- Import existing functions: `get_github_token`, `get_repository_identifier`
- Do NOT use `get_authenticated_username()` — it creates an internal client whose `oauth_scopes` are inaccessible. Instead, create a `Github` client directly to get both the user login (check 2) and scopes (check 1 value).
- Import `BaseGitHubManager` for repo access check
- Create `Github` client for `get_user()` / `oauth_scopes` (separate from `BaseGitHubManager`'s client)
- Each check wrapped in its own try/except — independent reporting
- `overall_ok` = all error-severity checks passed

## ALGORITHM

```
result = {}
# Check 1: token — call get_github_token(), report scopes later
token = get_github_token()
result["token_configured"] = ok/fail based on token being a string

# Check 2: auth — create a NEW Github(auth=Auth.Token(token)) client, call get_user()
# Do NOT use get_authenticated_username() — we need the client for oauth_scopes
try:
    github_client = Github(auth=Auth.Token(token))
    user = github_client.get_user()
    result["authenticated_user"] = ok with user.login
    # Now oauth_scopes is populated — update check 1 value
    scopes = github_client.oauth_scopes
    # Update token_configured value with scopes
except Exception:
    result["authenticated_user"] = fail
    # token_configured value stays "configured (scopes: unknown)"

# Check 3: repo URL — call get_repository_identifier(project_dir)
identifier = get_repository_identifier(project_dir)
result["repo_url"] = ok/fail based on identifier, use identifier.https_url as value

# Check 4: repo accessible — create BaseGitHubManager, call _get_repository()
# BaseGitHubManager raises ValueError if token is None — catch for independence
try:
    manager = BaseGitHubManager(project_dir=project_dir, github_token=token)
    repo = manager._get_repository()
    result["repo_accessible"] = ok/fail based on repo
except (ValueError, Exception):
    repo = None
    manager = None
    result["repo_accessible"] = fail with error message

# Checks 5-9: placeholder (Step 3)
# ... branch protection checks ...

result["overall_ok"] = all error-severity checks have ok=True
return result
```

### Key detail: Exception handling for check independence

When `token` is `None`:
- Check 2: `Github(auth=Auth.Token(None))` will fail → catch in try/except
- Check 4: `BaseGitHubManager(github_token=None)` raises `ValueError` → catch in try/except

Each check must have its own try/except to ensure later checks still run and report.

### Key detail: `oauth_scopes` ordering

`Github.oauth_scopes` is `None` until the first API call. The orchestrator:
1. Checks token exists (check 1 initial)
2. Calls `get_user()` (check 2) — this populates `oauth_scopes`
3. Updates check 1's `value` field with scopes

If check 2 fails, check 1 still reports `ok: True` but with `"configured (scopes: unknown)"`.

### Key detail: `BaseGitHubManager` with explicit token

Pass `github_token=token` to reuse the already-fetched token when available. When `token` is `None`, the constructor will attempt its own lookup and raise `ValueError`, which the try/except handles. Use `project_dir` mode since we have the path.

## DATA

Return dict (checks 1–4 only in this step, 5–9 added in Step 3):

```python
{
    "overall_ok": True,
    "token_configured": {"ok": True, "value": "configured (scopes: repo, workflow)", "severity": "error"},
    "authenticated_user": {"ok": True, "value": "username", "severity": "error"},
    "repo_url": {"ok": True, "value": "https://github.com/owner/repo", "severity": "error"},
    "repo_accessible": {"ok": True, "value": "owner/repo", "severity": "error"},
}
```

## TESTS

Test file: `tests/github_operations/test_verification.py`

| Test | Setup | Assertion |
|------|-------|-----------|
| `test_all_connectivity_checks_pass` | Mock all dependencies to succeed | All 4 checks `ok: True`, `overall_ok: True` |
| `test_token_not_configured` | `get_github_token()` returns `None` | `token_configured.ok = False`, `overall_ok = False` |
| `test_token_configured_scopes_reported` | Token exists, `oauth_scopes` returns `["repo", "workflow"]` | `value` contains `"repo, workflow"` |
| `test_auth_failure` | `get_user()` raises exception | `authenticated_user.ok = False`, `overall_ok = False` |
| `test_auth_failure_scopes_unknown` | `get_user()` raises, token exists | `token_configured.value` contains `"unknown"` |
| `test_repo_url_not_resolvable` | `get_repository_identifier()` returns `None` | `repo_url.ok = False`, `overall_ok = False` |
| `test_repo_not_accessible` | `_get_repository()` returns `None` | `repo_accessible.ok = False`, `overall_ok = False` |
| `test_checks_independent_token_fails_others_still_run` | Token `None` | All 4 check keys present in result |
| `test_checks_independent_auth_fails_repo_checks_still_run` | Auth fails | `repo_url` and `repo_accessible` still reported |

Mock strategy: patch `get_github_token`, `Github` class, `get_repository_identifier`, and `BaseGitHubManager` internals. Use `repo_url` mode or patch git repo detection to avoid needing a real git repo.

## COMMIT

```
feat: add verify_github() with connectivity checks (#157)
```
