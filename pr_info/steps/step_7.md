# Step 7 — `verify_github` diagnostics: split-except + DEBUG + `token_fingerprint`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 7 only: extend
> `verify_github()` in `src/mcp_workspace/github_operations/verification.py`
> with failure-path DEBUG logging and the `token_fingerprint` field on
> `token_configured`. Three coupled additions to one function, in one commit:
>
> 1. Split the auth-probe `except Exception` into
>    `except GithubException` (rich DEBUG via `_diagnostics`) and
>    `except Exception` (plain `str(exc)` DEBUG).
> 2. Extend the `CheckResult` TypedDict with `token_fingerprint: NotRequired[str]`.
> 3. Populate `token_fingerprint` on `result["token_configured"]` whenever a
>    token loaded (success or failure of auth probe).
>
> Use substring `caplog.text` checks; the only strict assertion is
> raw-token-not-in-logs. Follow TDD: extend
> `tests/github_operations/test_verification.py` first. Run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`)
> until all pass. Commit with message:
> `feat(github_operations): debug-log verify_github auth probe + add token_fingerprint`.

## WHERE

- **Modify**: `src/mcp_workspace/github_operations/verification.py`
- **Modify**: `tests/github_operations/test_verification.py`

## WHAT

```python
class CheckResult(TypedDict):
    ok: bool
    value: str
    severity: Literal["error", "warning"]
    error: NotRequired[str]
    install_hint: NotRequired[str]
    token_source: NotRequired[Literal["env", "config"]]
    token_fingerprint: NotRequired[str]   # NEW
```

`verify_github()` auth-probe block becomes:
```python
try:
    github_client = Github(auth=Auth.Token(token), base_url=api_base_url)
    user = github_client.get_user()
    result["authenticated_user"] = CheckResult(ok=True, value=user.login, severity="error")
    ...
except GithubException as e:
    logger.debug(
        "verify_github auth probe GithubException base_url=%s status=%s data=%s headers=%s token=%s",
        api_base_url, e.status, e.data, extract_diagnostic_headers(e),
        format_token_fingerprint(token) if token else "<none>",
    )
    result["authenticated_user"] = CheckResult(ok=False, value="authentication failed", severity="error", error=str(e))
except Exception as exc:
    logger.debug("verify_github auth probe error: %s", exc)
    result["authenticated_user"] = CheckResult(ok=False, value="authentication failed", severity="error", error=str(exc))
```

`token_configured` block:
```python
else:
    token_check = CheckResult(
        ok=True,
        value=f"configured (scopes: {scope_str or 'unknown'})",
        severity="error",
    )
    if source is not None:
        token_check["token_source"] = source
    token_check["token_fingerprint"] = format_token_fingerprint(token)   # NEW
    result["token_configured"] = token_check
```

## HOW

- New imports in `verification.py`:
  - `from mcp_workspace.github_operations._diagnostics import extract_diagnostic_headers`
  - `from mcp_workspace.utils.token_fingerprint import format_token_fingerprint`
- The `token_fingerprint` is populated only when `token is not None` (mirrors `token_source`).
- The `GithubException` `except` clause must catch `github.GithubException` specifically — `from github.GithubException import GithubException` is already imported.

## ALGORITHM

```
# In auth probe (replaces existing single broad except):
try: ... probe ...
except GithubException as e:
    logger.debug("verify_github auth probe GithubException base_url=%s status=%s data=%s headers=%s token=%s",
                 api_base_url, e.status, e.data, extract_diagnostic_headers(e),
                 format_token_fingerprint(token) if token else "<none>")
    result["authenticated_user"] = CheckResult(ok=False, value="authentication failed", severity="error", error=str(e))
except Exception as exc:
    logger.debug("verify_github auth probe error: %s", exc)
    result["authenticated_user"] = CheckResult(ok=False, value="authentication failed", severity="error", error=str(exc))

# In token-configured branch (when token is not None):
token_check["token_fingerprint"] = format_token_fingerprint(token)
```

## DATA

- `CheckResult` TypedDict gains `token_fingerprint: NotRequired[str]`
- `token_configured` `CheckResult` includes `token_fingerprint` whenever a token loaded
- DEBUG content reachable via `caplog.text` substring assertions (failure-path only)

## Tests (extend test_verification.py)

Set `caplog.set_level(logging.DEBUG, logger="mcp_workspace.github_operations.verification")`.

- `TestTokenFingerprintPopulated`:
  - All-OK run with token `"ghp_testtoken_abcdef..."` → `result["token_configured"]["token_fingerprint"]` starts with `"ghp_..."`
  - Auth-probe failure with token loaded → `token_fingerprint` STILL populated on `token_configured`
  - No token loaded (`token=None`) → `"token_fingerprint" not in result["token_configured"]`

- `TestAuthProbeDebugGithubException`:
  - Mock `get_user()` to raise `GithubException(401, {"message": "Bad credentials"}, headers={"X-GitHub-Request-Id": "abc"})`
  - `"status=401" in caplog.text`
  - `"Bad credentials" in caplog.text`
  - `"X-GitHub-Request-Id" in caplog.text`
  - `"base_url=" in caplog.text`
  - `"token=ghp_..." in caplog.text` (fingerprint, not raw)

- `TestAuthProbeDebugGenericException`:
  - Mock `get_user()` to raise `RuntimeError("connection reset by peer")`
  - `"connection reset by peer" in caplog.text`
  - `"status=" not in caplog.text` (rich-DEBUG branch did not fire)

- `TestRawTokenNotLogged` (strict negative):
  - Configured token: `"ghp_RAW_SECRET_TOKEN_VALUE_FOR_TEST_xyz"`
  - Trigger 401 GithubException
  - `"RAW_SECRET_TOKEN_VALUE_FOR_TEST" not in caplog.text`
  - Trigger generic Exception path → same negative
