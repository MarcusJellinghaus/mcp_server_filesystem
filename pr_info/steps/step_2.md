# Step 2 — Render exception detail in `format_pr_feedback`

## LLM Prompt

Read `pr_info/steps/summary.md` for full context, then implement Step 2 as described in this file.

**Prerequisite:** Step 1 must already be merged — `PRFeedback.unavailable` is `dict[str, Exception]` and `get_pr_feedback()` stores the raw exception per section.

**Apply TDD:** rewrite `TestUnavailableSection` to specify the new output formats first, watch them fail, then implement `_render_exception` and update the iteration loop until they pass. After implementation, run all three code-quality checks (pylint, pytest, mypy) and ensure they pass before committing.

---

## WHERE

| File | Change |
| ---- | ------ |
| `src/mcp_workspace/checks/pr_feedback.py` | New private helper + updated iteration loop + 2 imports |
| `tests/checks/test_branch_status_pr_feedback.py` | `TestUnavailableSection` class docstring + rewritten tests |

## WHAT

### Production code — `pr_feedback.py`

#### New imports at the top of the module

```python
import re

from github.GithubException import GithubException
```

#### New private helper

```python
def _render_exception(exc: Exception) -> str:
    """Render an exception as a single-line string for the [unavailable] section.

    Returns the portion that follows '<section>: '. Truncated at 200 chars
    with '...' appended if exceeded.
    """
```

Module-private (underscore prefix). Not re-exported. Lives next to `format_pr_feedback` in `pr_feedback.py`.

#### Updated iteration loop inside `format_pr_feedback` (replacing the existing 2-line block)

```python
for section, exc in unavailable.items():
    lines.append(f"[unavailable] {section}: {_render_exception(exc)}")
```

## HOW

- Both new imports go in `pr_feedback.py` only; no other module touched.
- `_render_exception` is private to `pr_feedback.py`; not added to `__all__` or any export list.
- The empty-state guard `if not blocking and not comments and not unavailable` is **unchanged** — empty dict remains falsy.
- No change to `collect_pr_feedback`.

## ALGORITHM

```
def _render_exception(exc):
    type_name = type(exc).__name__
    if isinstance(exc, GithubException):
        raw = exc.data.get("message") if isinstance(exc.data, dict) else None
        msg = re.sub(r"\s+", " ", raw).strip() if raw else ""
        rendered = f"{type_name} {exc.status}" + (f" — {msg}" if msg else "")
    else:
        msg = re.sub(r"\s+", " ", str(exc)).strip()
        rendered = f"{type_name} — {msg or '(no message)'}"
    return (rendered[:200] + "...") if len(rendered) > 200 else rendered
```

Notes:
- `type(exc).__name__` resolves to the **most-derived** class (e.g., `RateLimitExceededException`), so we never have to hardcode `"GithubException"`.
- For `GithubException` with no extractable message, the `— …` segment is **omitted entirely** (no `(no message)` placeholder, no `str(exc)` fallback — PyGithub's `__str__` starts with the status and would duplicate).
- The em-dash character is `—` (U+2014), as specified by the issue.

## DATA

Returns `str` — the part after `<section>: ` in the final line.

| Input                                                          | Returned                                            |
| -------------------------------------------------------------- | --------------------------------------------------- |
| `GithubException(500, {"message": "Server Error"}, ...)`       | `"GithubException 500 — Server Error"`              |
| `GithubException(500, {}, ...)`                                | `"GithubException 500"`                             |
| `GithubException(500, {"message": "   "}, ...)`                | `"GithubException 500"` (whitespace-only → omitted) |
| `ConnectionError("getaddrinfo failed")`                        | `"ConnectionError — getaddrinfo failed"`            |
| `RuntimeError("   ")`                                          | `"RuntimeError — (no message)"`                     |
| `GithubException(500, {"message": "boom\nsecond line"}, ...)`  | `"GithubException 500 — boom second line"`          |
| `GithubException(500, {"message": "x" * 500}, ...)`            | first 200 chars of the assembled line + `"..."`     |

---

## Test Updates — `tests/checks/test_branch_status_pr_feedback.py`

### Class docstring

`TestUnavailableSection`'s docstring changes from `"""Unavailable sections render placeholder lines."""` to something like `"""Unavailable sections render rich error detail per exception."""`.

### Replace existing two tests with these cases

Each fixture builds a `PRFeedback` via `_empty_feedback()` and sets `feedback["unavailable"] = {...}`.

1. **`GithubException` with extractable message**
   ```python
   feedback["unavailable"] = {
       "threads": GithubException(500, {"message": "Server Error"}, None)
   }
   assert "[unavailable] threads: GithubException 500 — Server Error" in result
   ```

2. **`GithubException` with empty `data` (no extractable message)** — message segment omitted
   ```python
   feedback["unavailable"] = {"threads": GithubException(500, {}, None)}
   # Assert the line is exactly "[unavailable] threads: GithubException 500"
   # with no " — " suffix and no "(no message)" placeholder.
   assert "[unavailable] threads: GithubException 500" in result
   assert "GithubException 500 —" not in result
   assert "(no message)" not in result
   ```

3. **`GithubException` with non-dict `data`** — `isinstance(exc.data, dict)` guard
   ```python
   feedback["unavailable"] = {"threads": GithubException(500, "raw text", None)}
   # The data attribute is a string (not a dict), so the isinstance guard
   # in _render_exception falls through to the empty-message branch:
   # the message segment is omitted entirely.
   assert "[unavailable] threads: GithubException 500" in result
   assert "GithubException 500 —" not in result
   assert "(no message)" not in result
   ```

4. **Generic exception with message**
   ```python
   feedback["unavailable"] = {"comments": ConnectionError("getaddrinfo failed")}
   assert "[unavailable] comments: ConnectionError — getaddrinfo failed" in result
   ```

5. **Generic exception with whitespace-only message → `(no message)`**
   ```python
   feedback["unavailable"] = {"alerts": RuntimeError("   ")}
   assert "[unavailable] alerts: RuntimeError — (no message)" in result
   ```

6. **Multi-line message collapsed to single spaces**
   ```python
   feedback["unavailable"] = {
       "threads": GithubException(500, {"message": "boom\nsecond line"}, None)
   }
   assert "[unavailable] threads: GithubException 500 — boom second line" in result
   ```

7. **Truncation at 200 chars**
   ```python
   feedback["unavailable"] = {
       "threads": GithubException(500, {"message": "x" * 500}, None)
   }
   line = next(l for l in result.split("\n") if l.startswith("[unavailable] threads: "))
   payload = line[len("[unavailable] threads: "):]
   assert payload.endswith("...")
   assert len(payload) == 203  # 200 chars + "..."
   ```

8. **Multiple sections preserved in insertion order (threads → comments → alerts)**
   ```python
   feedback["unavailable"] = {
       "threads": GithubException(500, {"message": "a"}, None),
       "comments": GithubException(502, {"message": "b"}, None),
       "alerts": GithubException(503, {"message": "c"}, None),
   }
   lines = result.split("\n")
   t_idx = next(i for i, l in enumerate(lines) if l.startswith("[unavailable] threads"))
   c_idx = next(i for i, l in enumerate(lines) if l.startswith("[unavailable] comments"))
   a_idx = next(i for i, l in enumerate(lines) if l.startswith("[unavailable] alerts"))
   assert t_idx < c_idx < a_idx
   ```

`GithubException` is imported from `github.GithubException` at the top of the test file (already used elsewhere in the test suite — add the import if not present).

---

## Verification

Run via MCP tools (see `.claude/CLAUDE.md` for required flags):

- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
- `mcp__mcp-tools-py__run_mypy_check`

All three must pass before committing.

## Commit

One commit covering both files. Suggested message:

```
fix(pr_feedback): surface underlying error in [unavailable] lines

Render exception type, status (for GithubException), and a one-line
message in PR Reviews '[unavailable]' rows. Hides the prior opaque
'API error' placeholder by using the per-section exception stored
in PRFeedback.unavailable.

Closes #199
```
