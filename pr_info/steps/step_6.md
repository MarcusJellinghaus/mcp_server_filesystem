# Step 6 — `verify_github` bug fix: identifier-first order + `api_base_url` to auth probe + new result entry

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 6 only: fix the
> auth-probe host bug in `verify_github()` in
> `src/mcp_workspace/github_operations/verification.py`. Three changes in one
> commit, all part of the same bug fix:
>
> 1. Reorder so the repository identifier resolves **before** the auth probe.
> 2. Pass `base_url=identifier.api_base_url` (or fallback `https://api.github.com`)
>    to the auth-probe `Github(...)` constructor.
> 3. Insert a new `api_base_url: CheckResult` entry as the **first** key of the
>    result dict (success: `severity="error"`; identifier-fallback:
>    `severity="warning"` so it does not poison `overall_ok`).
>
> Do **not** add DEBUG logging or `token_fingerprint` here — those land in
> Step 7. Follow TDD: extend `tests/github_operations/test_verification.py`
> first. Use constructor-kwarg assertion (not wrong-host simulation) to prove
> the fix. Run `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`,
> and `mcp__tools-py__run_pytest_check` (with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`)
> until all pass. Commit with message:
> `fix(github_operations): verify_github auth probe uses repo's API base URL`.

## WHERE

- **Modify**: `src/mcp_workspace/github_operations/verification.py`
- **Modify**: `tests/github_operations/test_verification.py`

## WHAT

`verify_github()` signature unchanged:
```python
def verify_github(project_dir: Path) -> dict[str, object]: ...
```

Internal control-flow change:
1. Resolve `identifier = get_repository_identifier(project_dir)` **first** (was after auth probe).
2. Compute `api_base_url = identifier.api_base_url if identifier else "https://api.github.com"`.
3. Insert `result["api_base_url"] = CheckResult(...)` as the **first** key.
4. Call `Github(auth=Auth.Token(token), base_url=api_base_url)` in the auth probe.
5. Then continue with token check, repo URL check (which already uses identifier), repo accessible, branch protection, etc.

## HOW

- No new imports.
- No new helper functions.
- Result-dict insertion order matters — Python dicts preserve insertion order. Insert `api_base_url` as the first assignment to `result`.
- The existing repo URL check (`result["repo_url"]`) keeps its current behavior — it still reports `error` when the identifier is None, so `overall_ok` is still poisoned by the underlying issue (just not by `api_base_url`).

## ALGORITHM

```
result = {}
token, source = get_github_token_with_source()

# Identifier first (was previously after auth)
try: identifier = get_repository_identifier(project_dir)
except Exception: identifier = None

api_base_url = identifier.api_base_url if identifier else "https://api.github.com"

# api_base_url FIRST entry
if identifier:
    result["api_base_url"] = CheckResult(ok=True, value=api_base_url, severity="error")
else:
    # severity="warning" (not "error") so this entry does NOT poison overall_ok:
    # the underlying error is already reported by result["repo_url"], and we do
    # not want a missing identifier to be counted twice in the failure set.
    result["api_base_url"] = CheckResult(
        ok=False,
        value=f"{api_base_url} (fallback - identifier unresolved)",
        severity="warning",
        error="Could not determine repository URL from git remote",
    )

# Auth probe — now passes base_url
try:
    github_client = Github(auth=Auth.Token(token), base_url=api_base_url)
    user = github_client.get_user()
    result["authenticated_user"] = CheckResult(ok=True, value=user.login, severity="error")
    ...
except Exception as exc:
    logger.debug("Authentication check failed: %s", exc)
    result["authenticated_user"] = CheckResult(ok=False, value="authentication failed", severity="error", error=str(exc))

# Token check (unchanged)
# Repo URL check (unchanged — uses identifier already computed above)
# Repo accessible, branch protection, etc. (unchanged)
```

## DATA

- New result key `api_base_url`: `CheckResult` with:
  - **success**: `ok=True`, `value=<API URL>`, `severity="error"` (passes overall_ok)
  - **fallback**: `ok=False`, `value="https://api.github.com (fallback - identifier unresolved)"`, `severity="warning"`, `error="..."` (does NOT poison overall_ok by itself)
- Final dict order: `api_base_url`, `authenticated_user`, `token_configured`, `repo_url`, `repo_accessible`, branch protection (5–9), `auto_delete_branches`, `overall_ok`
- All other keys unchanged in shape

## Tests (extend test_verification.py)

Update existing `_patch_all_ok` helper so the mocked identifier exposes both `https_url` AND `api_base_url`. New small helper takes `api_base_url` as an explicit parameter so the test does not depend on `hostname_to_api_base_url()` (production code) — if that helper's output changes, these tests must not break:

```python
def _make_identifier(
    hostname: str = "github.com",
    full_name: str = "owner/repo",
    api_base_url: str = "https://api.github.com",
) -> Mock:
    m = Mock()
    m.https_url = f"https://{hostname}/{full_name}"
    m.api_base_url = api_base_url           # explicit, not derived
    m.full_name = full_name
    return m
```

Tests that need the GHE shape pass it directly, e.g.:

```python
identifier = _make_identifier(
    hostname="tenant.ghe.com",
    api_base_url="https://api.tenant.ghe.com",
)
# and for GHES:
identifier = _make_identifier(
    hostname="ghe.example.com",
    api_base_url="https://ghe.example.com/api/v3",
)
```

New test classes:

- `TestAuthProbeBaseUrlGithubCom`: assert `mock_github_class.call_args.kwargs["base_url"] == "https://api.github.com"` for `github.com` hostname.
- `TestAuthProbeBaseUrlGhe`: identifier hostname `tenant.ghe.com` → assert `kwargs["base_url"] == "https://api.tenant.ghe.com"` (mirrors `test_ghe_project_dir_creates_client_with_ghe_base_url` pattern).
- `TestAuthProbeBaseUrlFallback`: `get_repository_identifier` returns `None` → assert `kwargs["base_url"] == "https://api.github.com"`.
- `TestApiBaseUrlResultEntrySuccess`: `result["api_base_url"]["ok"] is True`, value matches identifier's API URL, `severity == "error"`.
- `TestApiBaseUrlResultEntryFallback`: identifier `None` → `result["api_base_url"]["ok"] is False`, value contains `"fallback"`, `severity == "warning"`, `error` is set.
- `TestApiBaseUrlIsFirstKey`: `next(iter(result.keys())) == "api_base_url"`.
- `TestOverallOkNotPoisonedByFallback`: identifier `None` (auth + token can pass or fail — see explicit assertions below). The point is to prove that the `api_base_url` fallback entry does NOT cause `overall_ok=False`; the failure signal must come from `repo_url`. Concrete assertions:
  - `result["overall_ok"]["ok"] is False`
  - `result["repo_url"]["ok"] is False` and `result["repo_url"]["severity"] == "error"` (the contributing failure)
  - `result["api_base_url"]["ok"] is False` (it is unhappy)
  - `result["api_base_url"]["severity"] == "warning"` (but excluded from the overall_ok error set)
  - Optional reinforcement: temporarily flip `repo_url` to `ok=True` in a sibling test variant (or mock the overall_ok aggregator inputs) and assert `overall_ok` is True even with `api_base_url.ok=False severity=warning` — proves the warning entry alone cannot poison overall_ok.

Existing tests in `test_verification.py` that mock `identifier` need their mocks updated to also expose `api_base_url` (use the `_make_identifier` helper or set `.api_base_url` on existing `Mock()`).
