# Step 5 — DEBUG in `get_authenticated_username()` GithubException path

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 5 only: split the
> broad `except Exception` in `get_authenticated_username()` (in
> `src/mcp_workspace/github_operations/base_manager.py`) into
> `except GithubException` (DEBUG-log via `_diagnostics`, then re-raise as
> `ValueError`) and `except Exception` (existing behavior). Add tests in
> `tests/github_operations/test_base_manager.py` for substring DEBUG checks and
> a raw-token-not-in-logs negative. Follow TDD: write tests first. Run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`)
> until all pass. Commit with message:
> `feat(github_operations): debug-log GithubException in get_authenticated_username`.

## WHERE

- **Modify**: `src/mcp_workspace/github_operations/base_manager.py`
- **Modify**: `tests/github_operations/test_base_manager.py`

## WHAT

```python
def get_authenticated_username(hostname: Optional[str] = None) -> str:
    """(unchanged signature; behavior: still raises ValueError on any failure)"""
```

Internally split the existing broad `except Exception` into:
- `except GithubException as e:` → DEBUG-log status, data, allow-listed headers, `base_url`; re-raise as `ValueError(f"Failed to authenticate with GitHub: {e}")`
- `except Exception as e:` → unchanged: re-raise as `ValueError(...)` (no rich DEBUG — network/SSL errors lack status/data/headers)

## HOW

- Reuse the existing import added in Step 4: `from mcp_workspace.github_operations._diagnostics import extract_diagnostic_headers`.
- The `ValueError` re-raise message format must remain compatible with existing callers / tests — preserve `"Failed to authenticate with GitHub: {e}"`.

## ALGORITHM

```
try:
    base_url = hostname_to_api_base_url(hostname or "github.com")
    github_client = Github(auth=Auth.Token(raw_token), base_url=base_url)
    return github_client.get_user().login
except GithubException as e:
    logger.debug("get_authenticated_username GithubException status=%s data=%s headers=%s base_url=%s",
                 e.status, e.data, extract_diagnostic_headers(e), base_url)
    raise ValueError(f"Failed to authenticate with GitHub: {e}") from e
except Exception as e:
    raise ValueError(f"Failed to authenticate with GitHub: {e}") from e
```

Note: `base_url` must be assigned **before** the `try`'s API call (or computed inside both branches) so it is available in the `except`. Simplest: compute `base_url` before the `try`.

## DATA

- Return type unchanged: `str`
- Raises: `ValueError` (unchanged; from both `except` branches)
- DEBUG content reachable via `caplog.text` substring assertions

## Tests (write first)

Set `caplog.set_level(logging.DEBUG, logger="mcp_workspace.github_operations.base_manager")`. Mock `Github(...).get_user()` to raise `GithubException(401, {"message": "Bad credentials"}, headers={"X-GitHub-Request-Id": "abc"})`.

- `pytest.raises(ValueError, match="Failed to authenticate with GitHub")` — existing contract preserved
- `"status=401" in caplog.text`
- `"Bad credentials" in caplog.text`
- `"X-GitHub-Request-Id" in caplog.text`
- `"base_url=" in caplog.text`
- Generic `RuntimeError("connection reset")` → `ValueError` raised with same message format; **no** rich DEBUG content emitted (the GithubException-only DEBUG line not present)
- **Strict negative**: configured token `"ghp_RAW_SECRET_..."` not in `caplog.text` after 401
