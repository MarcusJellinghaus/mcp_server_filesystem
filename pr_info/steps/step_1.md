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

### WHAT — New test functions

| Test | Asserts |
|------|---------|
| `test_github_search_auto_injects_qualifiers` | When query has no `is:` qualifier, the query passed to `search_issues` contains `is:issue is:pull-request`, and result contains `"(auto-added: is:issue is:pull-request)"` |
| `test_github_search_preserves_explicit_is_issue` | When query contains `is:issue`, no injection occurs, no note in result |
| `test_github_search_preserves_explicit_is_pull_request` | When query contains `is:pull-request`, no injection occurs, no note in result |
| `test_github_search_case_insensitive_detection` | When query contains `Is:Issue` (mixed case), no injection occurs |
| `test_github_search_no_false_positive_on_substring` | When query contains `"this:issue"` (not a real qualifier), injection DOES occur |

### HOW
Each test follows the same pattern as existing `test_github_search_*` tests: mock `IssueManager`, set up `mock_repo.full_name`, call `github_search()`, inspect `call_args` on `search_issues` and the returned result string.

### DATA — Test inputs and expected behavior

```
"MCP migration"           → injects, note present
"MCP migration is:issue"  → no inject, no note
"fix is:pull-request"     → no inject, no note
"fix Is:Issue"            → no inject, no note (case-insensitive)
"this:issue problem"      → injects (substring, not real qualifier)
```

---

## Part B: Implementation

### WHERE
`src/mcp_workspace/server.py` — `github_search()` function (lines 623–686).

### WHAT — Changes

1. Add `import re` to the imports at the top of the file (line 1 area).
2. Add qualifier detection + injection before line 656 (`full_query = ...`).
3. Append note to result after line 684 (`return format_search_results(...)`).

### ALGORITHM (pseudocode, ~5 lines)

```python
# Before building full_query (line 656):
has_qualifier = re.search(r'(?:^|\s)is:(issue|pull-request)', query, re.IGNORECASE)
if not has_qualifier:
    query = query + " is:issue is:pull-request"

# After format_search_results (line 684):
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
