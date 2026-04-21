# Step 1: Auto-inject is:issue/is:pull-request qualifier in github_search

> **Reference:** See `pr_info/steps/summary.md` for full context (Issue #123).

## Overview

Add qualifier detection and auto-injection to `github_search()`, with tests. Single commit: tests + implementation + all checks passing.

## LLM Prompt

```
Implement Issue #123 (Step 1): In `github_search()` in `src/mcp_workspace/server.py`,
auto-inject `is:issue is:pull-request` into the query when neither qualifier is already
present. Use a case-insensitive word-boundary regex. Append a note to the result string
when qualifiers are auto-injected. Add tests in `tests/github_operations/test_github_read_tools.py`.
See pr_info/steps/summary.md and pr_info/steps/step_1.md for full details.
```

---

## Part A: Tests

### WHERE
`tests/github_operations/test_github_read_tools.py` — append to the existing `github_search` test section at the end of the file.

### UPDATE EXISTING TESTS

The following existing tests pass queries without `is:` qualifiers and will be affected by auto-injection. Update each to either add an explicit qualifier to the query or update assertions to expect injection:

- `test_github_search_basic` — passes `query="fix"` with no `is:` qualifier; update `call_args` assertion to expect injected qualifiers in the query, and result assertions to tolerate the appended note
- `test_github_search_empty` — passes `query="nonexistent"`; uses strict `assert result == "No results found."` which will break because the note is appended even to empty results; must change to `in` check or update expected string
- `test_github_search_with_qualifiers` — passes `query="bug"` (no `is:` qualifier despite the test name — it tests state/labels/sort params); update `call_kwargs["query"]` assertion to expect injected qualifiers
- `test_github_search_issue_vs_pr_indicator` — passes `query="test"`; the appended note adds an extra line that could affect `lines` indexing; verify assertions still hold or filter out the note line
- `test_github_search_max_results_cap` — passes `query="test"`; filters lines starting with `#` so the note line won't break the `len(lines)` check, but the query sent to `search_issues` will include injected qualifiers; likely no change needed but verify

The following tests are **not affected** (they error out before reaching injection logic):
- `test_github_search_error` — raises `RuntimeError` at `IssueManager()` construction, before any query processing
- `test_github_search_no_repo` — returns error when `_get_repository()` returns `None`, before query building

### WHAT — New parametrized test

Add a single `@pytest.mark.parametrize` test named `test_github_search_qualifier_injection` with columns `(query, should_inject, description)`:

| `query` | `should_inject` | `description` |
|---------|-----------------|---------------|
| `"MCP migration"` | `True` | `"no qualifier → injects"` |
| `"MCP migration is:issue"` | `False` | `"explicit is:issue → no inject"` |
| `"fix is:pull-request"` | `False` | `"explicit is:pull-request → no inject"` |
| `"fix Is:Issue"` | `False` | `"mixed case → no inject"` |
| `"basis:issue problem"` | `True` | `"substring containing is:issue → injects"` |

When `should_inject` is `True`, assert that the query passed to `search_issues` contains `is:issue is:pull-request` and the result contains `"(auto-added: is:issue is:pull-request)"`. When `False`, assert no injection and no note.

### HOW
The test follows the same pattern as existing `test_github_search_*` tests: mock `IssueManager`, set up `mock_repo.full_name`, call `github_search()`, inspect `call_args` on `search_issues` and the returned result string.

---

## Part B: Implementation

### WHERE
`src/mcp_workspace/server.py` — `github_search()` function (lines 623–686).

### WHAT — Changes

1. Add `import re` after `import logging` (alphabetical order among stdlib imports).
2. Add qualifier detection + injection before line 656 (`full_query = ...`).
3. Append note to result after line 684 (`return format_search_results(...)`).

### ALGORITHM (pseudocode, ~5 lines)

```python
# Before building full_query (line 656):
has_qualifier = re.search(r'(?:^|\s)is:(issue|pull-request)', query, re.IGNORECASE)
if not has_qualifier:
    query = query + " is:issue is:pull-request"

# Replace the direct return on line 684 with:
result = format_search_results(items, max_results)
if not has_qualifier:
    result += "\n(auto-added: is:issue is:pull-request)"
return result
```

### DATA — Return value change

When qualifiers are auto-injected, the return string has an extra trailing line:
```
#1 [Issue] [open] Bug fix
#2 [PR] [open] Feature PR
(auto-added: is:issue is:pull-request)
```

When qualifiers are already present, return value is unchanged from current behavior.

---

## Commit

```
fix: auto-inject is:issue/is:pull-request in github_search

When neither is:issue nor is:pull-request is present in the query,
auto-inject both qualifiers to prevent GitHub API 422 errors.
Appends a transparency note to the result when injection occurs.

Closes #123
```
