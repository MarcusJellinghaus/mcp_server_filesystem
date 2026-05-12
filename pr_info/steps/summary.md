# Issue #199 — Surface underlying error in PR Reviews `[unavailable]` lines

## Context

`check_branch_status`'s PR Reviews section renders `[unavailable] threads: API error` — an opaque placeholder that hides which API failed and why. The underlying exception is logged at `WARNING` level but discarded from the user-facing report.

Two data-flow points lose the detail:

1. `PullRequestManager.get_pr_feedback()` (`src/mcp_workspace/github_operations/pr_manager.py`) catches per-section exceptions, calls `logger.warning(...)`, but only appends the section *name* (`"threads"` / `"comments"` / `"alerts"`) into `PRFeedback.unavailable: list[str]`. The exception object is discarded.
2. `format_pr_feedback()` (`src/mcp_workspace/checks/pr_feedback.py`) renders those names with a hardcoded `": API error"` suffix.

## Goal

Carry the raw exception from `get_pr_feedback()` through to `format_pr_feedback()`. Render exception type, status (for `GithubException`), and a single-line message — without changing the structure of the PR Reviews block.

## Architectural / Design Changes

### 1. Data shape change: `PRFeedback.unavailable`

| Before                  | After                          |
| ----------------------- | ------------------------------ |
| `list[str]` (section names) | `dict[str, Exception]` (section → raw exception) |

- `PRFeedback` is an **internal** TypedDict; the only in-repo consumer is `format_pr_feedback`. No compat shim, no migration path.
- Dict preserves insertion order (Python 3.7+); section order threads → comments → alerts comes naturally from append order in `get_pr_feedback`.
- Empty-state check (`if not unavailable`) works identically for `dict` and `list` — no formatter-logic change needed beyond the iteration site.

### 2. Rendering location

- Render exceptions in `format_pr_feedback` (presentation layer), **not** in `pr_manager.py` (data layer).
- A new file-local helper `_render_exception(exc: Exception) -> str` returns the portion after `<section>: `. No new module, no public API.

### 3. Rendering rules

- Exception type label: `type(e).__name__` — surfaces derived classes (e.g., `RateLimitExceededException`), not always the base `GithubException`.
- `GithubException`, message extractable from `e.data["message"]` → `ExceptionType STATUS — message`
- `GithubException`, message *not* extractable → `ExceptionType STATUS` (message segment omitted entirely; **no** `str(e)` fallback — PyGithub's `__str__` already starts with the status code, which would duplicate)
- Other exceptions → `ExceptionType — message`
- Other exceptions with empty / whitespace-only message → `ExceptionType — (no message)`
- Whitespace normalization: `re.sub(r"\s+", " ", msg).strip()` collapses newlines, tabs, and multiple spaces uniformly.
- Truncation: the assembled portion (after `<section>: `) is capped at 200 chars with `...` appended → max ~203 chars.

### Constraints preserved

- **Single line per section.** Maintains visual alignment with `[unresolved thread]`, `[comment]`, `[alert]` lines.
- `logger.warning(...)` path in `get_pr_feedback` keeps full exception detail for debugging — **unchanged**.
- 403 silent-skip on code-scanning alerts — **unchanged** (intentional token-permission behavior).
- `_handle_github_errors` decorator behavior (re-raising 401/403 at method level) — **unchanged**.
- Dict insertion order (threads → comments → alerts) — must not be refactored to an unordered container.

## Files Affected

### Modified

- `src/mcp_workspace/github_operations/pr_manager.py`
  - `PRFeedback` TypedDict: `unavailable: dict[str, Exception]`
  - `_empty_pr_feedback()`: `"unavailable": {}`
  - `get_pr_feedback()`: 3 sites — store exception under section key instead of appending section name

- `src/mcp_workspace/checks/pr_feedback.py`
  - New private helper `_render_exception(exc: Exception) -> str`
  - `format_pr_feedback()`: iteration site renders via the helper
  - New imports: `re`, `github.GithubException.GithubException`

- `tests/github_operations/test_pr_manager_feedback.py`
  - Update `unavailable` assertions from list shape to dict shape
  - Add `isinstance(value, Exception)` checks where appropriate

- `tests/checks/test_branch_status_pr_feedback.py`
  - `_empty_feedback` helper: `"unavailable": {}`
  - `TestUnavailableSection`: class docstring + tests rewritten for exception rendering

### Created

None.

### Deleted

None.

## Step Overview

| Step | Scope | User-visible behavior after step |
| ---- | ----- | -------------------------------- |
| 1    | Data-shape change in `pr_manager.py` + its tests; mechanical fixture updates in formatter tests | **Unchanged** — still `[unavailable] threads: API error` |
| 2    | Renderer in `pr_feedback.py` + rewritten `TestUnavailableSection` | **Fixed** — renders exception type, status, message per the spec |

Two steps, each one commit, each passing all checks independently. Step 1 lays the rails; Step 2 fixes the user-visible bug.
