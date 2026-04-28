# Step 2: Surface `token_source` in `verify_github()` `CheckResult`

> Implements the verification-layer half of [summary.md](summary.md). Depends on Step 1 (`get_github_token_with_source` must exist in `config.py`).

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Step 1 must already be merged/committed. Implement Step 2 only.
>
> TDD order (note: after step 1 alone, the existing tests will FAIL — the patch-site rename breaks them until `verify_github()` is refactored in step 2. Quality gates only need to pass after step 3.):
> 1. Extend the `_patch_all_ok` helper and update the 13 existing patch sites in `tests/github_operations/test_verification.py` (mechanical rename: `get_github_token` → `get_github_token_with_source`, scalar return values become tuples).
> 2. Implement the `CheckResult` TypedDict extension and refactor `verify_github()` to single-write `token_configured` and set `token_source`.
> 3. Add the four new `TestTokenSource` / auth-failure tests for `token_source`.
> 4. Run all quality gates — they should all be green now.
>
> Run `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check` (with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`), and `mcp__tools-py__run_mypy_check` — all must pass. Single commit.

## WHERE

- **Modify** `src/mcp_workspace/github_operations/verification.py`
- **Modify** `tests/github_operations/test_verification.py`

## WHAT

### Extend `CheckResult` TypedDict (verification.py)

```python
class CheckResult(TypedDict):
    ok: bool
    value: str
    severity: Literal["error", "warning"]
    error: NotRequired[str]
    install_hint: NotRequired[str]
    token_source: NotRequired[Literal["env", "config"]]  # NEW
```

### Refactor `verify_github()` token/auth section

Replace the existing token import and the double-write pattern (`token_configured` written at line ~51 and overwritten at line ~85) with a linear flow:

1. Call `get_github_token_with_source()` once to get `(token, source)`.
2. Run the auth try/except — write only `authenticated_user` and capture `scope_str` in a local variable (default `None` on failure).
3. Build `token_configured` **once** at the end of the section, populating `token_source` whenever `source is not None` (even on auth failure).

Other checks (3 — repo URL, 4 — repo accessible, 5–10 — branch protection / auto-delete) and `overall_ok` aggregation are **unchanged**.

## HOW

- **Imports note:** `from typing import Literal` is **already present** in `src/mcp_workspace/github_operations/verification.py` (line ~9, alongside `Any, NotRequired, TypedDict`) — do NOT re-add it. The only import change in that file is replacing `from mcp_workspace.config import get_github_token` with `from mcp_workspace.config import get_github_token_with_source`. Note that `get_github_token` is still used by `src/mcp_workspace/github_operations/base_manager.py` — leave that import alone (Step 1 keeps `get_github_token()` as a thin wrapper, so `base_manager.py` is unaffected).
- Replace `from mcp_workspace.config import get_github_token` with `from mcp_workspace.config import get_github_token_with_source` in `verification.py` only.
- Add `token_source: NotRequired[Literal["env", "config"]]` field to `CheckResult` (last field).
- In `tests/github_operations/test_verification.py`, replace all 13 occurrences of `f"{MODULE}.get_github_token"` with `f"{MODULE}.get_github_token_with_source"` and update return values:
  - `return_value="ghp_test"` → `return_value=("ghp_test", "env")` (or `"config"` where the test specifically targets the config path; default `"env"` is fine for tests that don't care)
  - `return_value=None` → `return_value=(None, None)`
- Update `_patch_all_ok` helper accordingly (the helper used across many tests — fix once, propagates).

## ALGORITHM

```
function verify_github(project_dir):
    (token, source) = get_github_token_with_source()
    scope_str = None
    try:
        client = Github(auth=Auth.Token(token))
        user = client.get_user()
        result["authenticated_user"] = ok-CheckResult(user.login)
        scope_str = format(client.oauth_scopes)   # "repo, workflow" | "none" | "unknown"
    except Exception as exc:
        result["authenticated_user"] = fail-CheckResult(str(exc))
    # Build token_configured ONCE
    if token is None:
        result["token_configured"] = fail-CheckResult(value="not configured", error=..., install_hint=...)
    else:
        value = f"configured (scopes: {scope_str or 'unknown'})"
        result["token_configured"] = ok-CheckResult(value)
        if source is not None:
            result["token_configured"]["token_source"] = source
    # ... rest of checks unchanged
```

## DATA

**`token_configured` `CheckResult` shape after Step 2:**

| Scenario | `ok` | `value` | `token_source` | Other fields |
|---|---|---|---|---|
| Token from env, auth succeeds | `True` | `"configured (scopes: …)"` | `"env"` | — |
| Token from config, auth succeeds | `True` | `"configured (scopes: …)"` | `"config"` | — |
| Token from env, auth fails | `True`* | `"configured (scopes: unknown)"` | `"env"` | — |
| No token at all | `False` | `"not configured"` | *(omitted)* | `error`, `install_hint` |

\* `ok=True` on `token_configured` even when auth fails matches existing behavior — auth failure is reported on `authenticated_user`, not on `token_configured`. The new field surfaces source on the (still-`ok`) token check, which is what consumers need to render an `[INFO]` line alongside the failed auth check.

## Tests (write first)

### Update existing tests (mechanical, ~13 patch sites)

| Find | Replace |
|---|---|
| `patch(f"{MODULE}.get_github_token", return_value="ghp_test")` | `patch(f"{MODULE}.get_github_token_with_source", return_value=("ghp_test", "env"))` |
| `patch(f"{MODULE}.get_github_token", return_value="ghp_testtoken")` | `patch(f"{MODULE}.get_github_token_with_source", return_value=("ghp_testtoken", "env"))` |
| `patch(f"{MODULE}.get_github_token", return_value=None)` | `patch(f"{MODULE}.get_github_token_with_source", return_value=(None, None))` |

### Add four new test methods

Add a new class `TestTokenSource` to `tests/github_operations/test_verification.py`:

```python
class TestTokenSource:
    def test_token_source_env(self, tmp_path: Path) -> None:
        # patch get_github_token_with_source -> ("ghp_x", "env")
        # all-OK path; assert result["token_configured"]["token_source"] == "env"

    def test_token_source_config(self, tmp_path: Path) -> None:
        # patch get_github_token_with_source -> ("ghp_x", "config")
        # all-OK path; assert result["token_configured"]["token_source"] == "config"

    def test_token_source_omitted_when_no_token(self, tmp_path: Path) -> None:
        # patch get_github_token_with_source -> (None, None)
        # assert "token_source" not in result["token_configured"]

    def test_token_source_set_on_auth_failure(self, tmp_path: Path) -> None:
        # patch get_github_token_with_source -> ("ghp_bad", "env")
        # mock client.get_user() to raise (e.g. 401 "Bad credentials")
        # assert result["authenticated_user"]["ok"] is False
        # assert result["token_configured"]["token_source"] == "env"
        # This is the motivating "Bad credentials" debug scenario from
        # Acceptance criterion 4 / Decision #7 — token_source MUST still
        # be set when the token resolves but auth then fails.
```

Reuse `_patch_all_ok` for the first two by parameterizing its mock return; for the third, use a minimal patch block similar to `TestTokenNotConfigured`. For the fourth, model it on the existing `TestAuthFailure` class — patch the token source as `"env"` and force `Github.get_user()` to raise (matching the existing auth-failure test pattern). If preferred, the fourth test can live inside `TestAuthFailure` instead of `TestTokenSource` — pick whichever organization is more idiomatic for this file.

`_patch_all_ok` will need a small extension: accept an optional `token_source: Literal["env", "config"] = "env"` parameter and forward it to the patched return tuple.

## Done When

- All 3 quality checks pass.
- All existing verification tests pass after the mechanical patch update.
- 4 new tests for `token_source` pass (3 in `TestTokenSource` + 1 auth-failure case, possibly in `TestAuthFailure`).
- `verify_github()` writes `token_configured` exactly once.
- Single commit on the working branch with the changes from this step only.
