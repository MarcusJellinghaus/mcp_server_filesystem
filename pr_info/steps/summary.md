# Summary: Expose `token_source` in `verify_github()` `CheckResult`

## Goal

Surface **which source** (env var vs config file) provided the GitHub token used by `verify_github()`, so downstream consumers (mcp-coder's `verify` CLI) can disambiguate precedence for users who have both `GITHUB_TOKEN` and `[github] token` configured. Without this, a stale env var silently shadows a config update — the motivating "Bad credentials" debugging scenario.

## Architectural / Design Changes

This change is **purely additive** to public APIs. No layer, contract, or import boundary changes.

| Concern | Change |
|---|---|
| `config.py` | Add sibling helper `get_github_token_with_source()`. Refactor existing `get_github_token()` into a thin wrapper around it — single source of truth for env→config precedence. Public signature of `get_github_token()` is preserved (`str \| None`), so `BaseGitHubManager` and ~100 mock sites are unaffected. |
| `verification.py` `CheckResult` TypedDict | Add optional `token_source: NotRequired[Literal["env", "config"]]`. |
| `verify_github()` token-resolution flow | Replace `get_github_token()` call with `get_github_token_with_source()`. Refactor: build `token_configured` **once** at the end of the token/auth section instead of writing at line 51 then overwriting at line 85. `token_source` is set whenever a token resolves — including when the subsequent auth check fails (the motivating debug case). |
| `get_test_repo_url()` | **Unchanged** — YAGNI; defer until a real consumer needs source disambiguation. |

### Behavioral contract

- `get_github_token_with_source()` returns `(token, "env")` when `GITHUB_TOKEN` is set, `(token, "config")` when falling through to `~/.mcp_coder/config.toml`, and `(None, None)` when neither source is configured.
- `verify_github()` outputs are unchanged except for the new `token_source` field on `token_configured`. Field is **omitted** when no token resolves; **present** whenever a token resolves (even if auth fails).

## Files Created / Modified

### Modified
- `src/mcp_workspace/config.py` — add `get_github_token_with_source()`; refactor `get_github_token()` to delegate.
- `src/mcp_workspace/github_operations/verification.py` — extend `CheckResult`; refactor token/auth flow in `verify_github()`.
- `tests/test_config.py` — add `TestGetGithubTokenWithSource` class (4 cases).
- `tests/github_operations/test_verification.py` — update 13 patch sites from `get_github_token` to `get_github_token_with_source` with tuple return values; add 4 new tests for `token_source` (env, config, omitted, and the auth-failure debug case).

### Created
- None.

### Deleted
- None.

## Implementation Steps

| # | Step | Scope |
|---|---|---|
| 1 | [step_1.md](step_1.md) | Add `get_github_token_with_source()` in `config.py` + tests; refactor `get_github_token()` to delegate. |
| 2 | [step_2.md](step_2.md) | Extend `CheckResult` with `token_source`; refactor `verify_github()` token/auth flow; update existing test mocks; add 3 new verification tests. |

Each step is one commit and runs all three quality gates (pylint, pytest, mypy) before being considered done.
