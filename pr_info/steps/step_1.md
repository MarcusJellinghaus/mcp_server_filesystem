# Step 1: Add `get_github_token_with_source()` helper

> Implements the config-layer half of [summary.md](summary.md). Sibling helper to `get_github_token()` that also returns the source (`"env"` | `"config"`).

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement Step 1 only.
>
> TDD order: write the tests first (they will fail), then add the helper, then refactor `get_github_token()` to delegate. Run `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check` (with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`), and `mcp__tools-py__run_mypy_check` — all must pass before the commit. Do not modify `verify_github()` or any verification code in this step. Single commit.

## WHERE

- **Modify** `src/mcp_workspace/config.py`
- **Modify** `tests/test_config.py`

## WHAT

### New function in `src/mcp_workspace/config.py`

```python
from typing import Literal

def get_github_token_with_source() -> tuple[str | None, Literal["env", "config"] | None]:
    """Resolve GitHub token with source: env var → config file → (None, None)."""
```

### Refactor existing function (same module)

```python
def get_github_token() -> str | None:
    """Resolve GitHub token: env var → config file → None."""
    return get_github_token_with_source()[0]
```

Public signature and behavior of `get_github_token()` are unchanged. No callers need updating.

## HOW

- Add `from typing import Literal` to `config.py` imports.
- Implement `get_github_token_with_source()` using the same env→config precedence already in `get_github_token()` (env var key `"GITHUB_TOKEN"`, config section `"github"`, config key `"token"`).
- Replace the body of `get_github_token()` with a delegation call to the new helper, preserving the docstring.
- Leave `get_test_repo_url()` and `_read_config_value()` untouched.

## ALGORITHM

```
function get_github_token_with_source():
    token = os.environ.get("GITHUB_TOKEN")
    if token: return (token, "env")
    token = _read_config_value("github", "token")
    if token: return (token, "config")
    return (None, None)
```

## DATA

**Return type:** `tuple[str | None, Literal["env", "config"] | None]`

| Scenario | Return value |
|---|---|
| `GITHUB_TOKEN` env var set | `(token, "env")` |
| Env var unset, config file has `[github] token` | `(token, "config")` |
| Neither configured (or malformed TOML) | `(None, None)` |

## Tests (write first)

In `tests/test_config.py`, add a new class `TestGetGithubTokenWithSource` mirroring the four existing `TestGetGithubToken` cases:

| Test | Setup | Expected |
|---|---|---|
| `test_returns_env_var_when_set` | `GITHUB_TOKEN=env_token` | `("env_token", "env")` |
| `test_falls_back_to_config_file` | env cleared, config has `token = "file_token"` | `("file_token", "config")` |
| `test_env_var_takes_precedence` | both env and config set | `("env_token", "env")` |
| `test_returns_none_when_neither_source` | env cleared, no config file | `(None, None)` |

Add `get_github_token_with_source` to the module's import line at the top of `tests/test_config.py`.

Existing `TestGetGithubToken` and `TestReadConfigValue` classes stay as-is — they validate that the refactored `get_github_token()` still works.

## Done When

- All 3 quality checks pass.
- 4 new test cases pass; all existing tests still pass.
- Single commit on the working branch with the changes from this step only.
