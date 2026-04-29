# Step 1 — Add `_diagnostics.py` shared helper module

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1 only: create
> `src/mcp_workspace/github_operations/_diagnostics.py` with the
> `DIAGNOSTIC_HEADERS` constant and `extract_diagnostic_headers()` helper, plus
> tests in `tests/github_operations/test_diagnostics.py`. Follow TDD: write the
> tests first, then the module. Run `mcp__tools-py__run_pylint_check`,
> `mcp__tools-py__run_mypy_check`, and `mcp__tools-py__run_pytest_check` (with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`)
> until all pass. Commit with message:
> `feat(github_operations): add _diagnostics helper for response-header extraction`.

## WHERE

- **Create**: `src/mcp_workspace/github_operations/_diagnostics.py`
- **Create**: `tests/github_operations/test_diagnostics.py`

## WHAT

```python
# _diagnostics.py
DIAGNOSTIC_HEADERS: frozenset[str]  # 7 lower-cased header names

def extract_diagnostic_headers(exc: GithubException) -> dict[str, str]:
    """Return only allow-listed headers from exc.headers (case-insensitive lookup)."""
```

## HOW

- Module-private (underscore prefix); not exported via `github_operations/__init__.py`.
- Imports: `from github.GithubException import GithubException` (already isolated to this layer).
- No external deps beyond `github` and stdlib.

## ALGORITHM

```
DIAGNOSTIC_HEADERS = frozenset of 7 names
  ("WWW-Authenticate", "X-OAuth-Scopes", "X-Accepted-OAuth-Scopes",
   "X-GitHub-Request-Id", "X-RateLimit-Remaining", "X-RateLimit-Limit", "Date")

extract_diagnostic_headers(exc):
    if exc.headers is None or empty: return {}
    allow_lower = {h.lower() for h in DIAGNOSTIC_HEADERS}
    return {k: v for k, v in exc.headers.items() if k.lower() in allow_lower}
```

## DATA

- `DIAGNOSTIC_HEADERS`: `frozenset[str]` — exact header names as documented in the issue
- Return: `dict[str, str]` — preserves original key casing from `exc.headers`; empty dict when no headers present or none match

## Tests (write first)

- Empty/None headers → `{}`
- Headers with all-listed entries → returned verbatim
- Headers with mixed listed + unlisted → only listed entries returned
- Lowercase keys (`"x-github-request-id"`) → matched and returned
- Mixed-case keys (`"X-GitHub-Request-Id"`) → matched and returned
- Unlisted headers (`"Set-Cookie"`, `"X-Proxy-Foo"`) → excluded
