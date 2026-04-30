# Step 4 — DEBUG companion in `BaseGitHubManager._get_repository()`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 4 only: add a
> DEBUG log call inside the existing `except GithubException` clause of
> `BaseGitHubManager._get_repository()` in
> `src/mcp_workspace/github_operations/base_manager.py`, using
> `extract_diagnostic_headers` from Step 1's `_diagnostics` module. Keep the
> existing user-friendly ERROR log untouched. Add tests in
> `tests/github_operations/test_base_manager.py` that substring-check the DEBUG
> output and a strict raw-token-not-in-logs negative. Follow TDD: write tests
> first. Run `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`,
> and `mcp__tools-py__run_pytest_check` (with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`)
> until all pass. Commit with message:
> `feat(github_operations): debug-log GithubException details in _get_repository`.

## WHERE

- **Modify**: `src/mcp_workspace/github_operations/base_manager.py`
- **Modify**: `tests/github_operations/test_base_manager.py`

## WHAT

- Inside `_get_repository()`'s `except GithubException as e:` block, add **one**
  `logger.debug(...)` call (in addition to the existing `logger.error(...)`).
- Log fields: `e.status`, `e.data`, allow-listed headers, `full_name`, `api_base_url`,
  `token` (fingerprint of `self.github_token`).

Signature unchanged:
```python
@log_function_call
def _get_repository(self) -> Optional[Repository]: ...
```

## HOW

- Add: `from mcp_workspace.github_operations._diagnostics import extract_diagnostic_headers`
- Add: `from mcp_workspace.utils.token_fingerprint import format_token_fingerprint`
- Within `except GithubException as e:` (before the existing 404-vs-other branching that emits ERROR):
  ```python
  logger.debug(
      "_get_repository GithubException status=%s data=%s headers=%s full_name=%s api_base_url=%s token=%s",
      e.status, e.data, extract_diagnostic_headers(e),
      self._repo_identifier.full_name, self._repo_identifier.api_base_url,
      format_token_fingerprint(self.github_token) if self.github_token else "<none>",
  )
  ```
- Order: emit DEBUG **before** the existing 404/other ERROR branch, so DEBUG is always emitted regardless of status.
- The manager's token attribute is `self.github_token` (set in `__init__` after token resolution).

## ALGORITHM

```
except GithubException as e:
    logger.debug("_get_repository ... status=... data=... headers=... full_name=... api_base_url=... token=...")
    repo_url = self._repo_identifier.https_url
    if e.status == 404:
        logger.error("Repository not found: %s ...", repo_url)
    else:
        logger.error("Failed to access repository %s: %s", repo_url, e)
    return None
```

## DATA

- No change to return type or behavior
- DEBUG content reachable via `caplog.text` substring assertions
- Headers field contains only allow-listed entries (or `{}` if none present)

## Tests (write first)

Set `caplog.set_level(logging.DEBUG, logger="mcp_workspace.github_operations.base_manager")`.

- 401 GithubException with allow-listed `WWW-Authenticate`, `X-GitHub-Request-Id` headers and a `{"message": "Bad credentials"}` body:
  - `"status=401" in caplog.text`
  - `"Bad credentials" in caplog.text`
  - `"X-GitHub-Request-Id" in caplog.text`
  - `"WWW-Authenticate" in caplog.text`
  - `"full_name=" in caplog.text`
  - `"api_base_url=" in caplog.text`
  - `"token=ghp_..." in caplog.text` (fingerprint of configured token, not raw)
- 404 GithubException → DEBUG emitted with `status=404`, **and** existing ERROR for "Repository not found" remains
- 500 GithubException with non-allow-listed `Set-Cookie` header → `caplog.text` does NOT contain `"Set-Cookie"`
- **Strict negative**: token `"ghp_RAW_SECRET_TOKEN_VALUE_FOR_TEST_xyz"` configured on manager; on 401 GithubException, raw token substring NOT in `caplog.text` (the fingerprint `ghp_..._xyz` IS present, but the full raw middle is not).
