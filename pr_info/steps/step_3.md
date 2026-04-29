# Step 3 — DEBUG logging in `hostname_to_api_base_url()`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 3 only: add
> DEBUG logging to `hostname_to_api_base_url()` in
> `src/mcp_workspace/utils/repo_identifier.py`, plus a substring `caplog.text`
> test in `tests/utils/test_repo_identifier.py`. Follow TDD: extend tests first,
> then update the function. The single happy-path DEBUG log here is intentional
> — the helper's branch decision is invisible elsewhere. Run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`)
> until all pass. Commit with message:
> `feat(utils): debug-log hostname_to_api_base_url branch decision`.

## WHERE

- **Modify**: `src/mcp_workspace/utils/repo_identifier.py`
- **Modify**: `tests/utils/test_repo_identifier.py`

## WHAT

- Add module-level `logger = logging.getLogger(__name__)` to `repo_identifier.py`.
- Add **single** `logger.debug(...)` call inside `hostname_to_api_base_url()` before each return, capturing input hostname, normalized form, matched branch, and resolved URL.

Function signature is unchanged:
```python
def hostname_to_api_base_url(hostname: str) -> str: ...
```

## HOW

- `import logging` at top of `repo_identifier.py`.
- One `logger.debug` per branch (3 branches: github.com, *.ghe.com, GHES fallback) — each emits `input`, `normalized`, `branch`, `url` in one line.

## ALGORITHM

```
h = hostname.lower()
if h == "github.com":
    url = "https://api.github.com"
    logger.debug("hostname_to_api_base_url input=%s normalized=%s branch=github.com url=%s", hostname, h, url)
    return url
elif h.endswith(".ghe.com"):
    url = f"https://api.{h}"
    logger.debug("... branch=ghe.com ...")
    return url
else:
    url = f"https://{hostname}/api/v3"
    logger.debug("... branch=ghes-fallback ...")
    return url
```

## DATA

- No change to return type/value
- DEBUG log content reachable via `caplog.text` substring assertions

## Tests (extend `tests/utils/test_repo_identifier.py`)

Use `caplog.set_level(logging.DEBUG, logger="mcp_workspace.utils.repo_identifier")`. Substring assertions only.

- `hostname_to_api_base_url("github.com")` → `caplog.text` contains `"branch=github.com"` and `"url=https://api.github.com"`
- `hostname_to_api_base_url("tenant.ghe.com")` → `caplog.text` contains `"branch=ghe.com"` and `"url=https://api.tenant.ghe.com"`
- `hostname_to_api_base_url("ghe.corp.com")` → `caplog.text` contains `"branch=ghes-fallback"` and `"url=https://ghe.corp.com/api/v3"`
- Mixed-case input `"GitHub.com"` → `caplog.text` contains `"input=GitHub.com"` and `"normalized=github.com"`
