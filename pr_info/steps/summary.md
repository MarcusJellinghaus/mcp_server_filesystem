# Issue #123: Auto-inject is:issue/is:pull-request qualifier in github_search

## Problem

`github_search` fails with a 422 error when the query doesn't include `is:issue` or `is:pull-request`, because GitHub's search API requires one of these qualifiers.

## Solution

Add qualifier detection before building `full_query` in `github_search()`. When neither `is:issue` nor `is:pull-request` is present, auto-inject both. Append a transparency note to the result string when injection occurs.

## Architectural / Design Changes

**No architectural changes.** This is a small behavioral fix contained entirely within the existing `github_search()` function in `server.py`. The change adds:

- One regex check (~1 line) to detect existing qualifiers
- One conditional append (~2 lines) to inject missing qualifiers
- One conditional string append (~2 lines) to add a transparency note to results

No new modules, classes, helpers, or abstractions are introduced. The formatter layer (`formatters.py`) is untouched — the note is appended at the call site in `server.py`.

**Design decisions (from issue):**
- No new `type` parameter — dedicated tools already cover filtered use cases
- Default `is:issue is:pull-request` (both) — least surprising behavior
- Respect explicit qualifiers — don't override user intent
- Case-insensitive word-boundary regex — avoids substring false positives
- Runtime note instead of docstring change — caller transparency

## Files Modified

| File | Action | Purpose |
|------|--------|---------|
| `src/mcp_workspace/server.py` | Modify | Add `import re`, add qualifier detection + injection logic in `github_search()` (~line 656), append note to result (~line 684) |
| `tests/github_operations/test_github_read_tools.py` | Modify | Add test cases for qualifier auto-injection, explicit qualifier passthrough, case-insensitivity, substring safety, and note presence |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Tests for qualifier auto-injection + production code | `fix: auto-inject is:issue/is:pull-request in github_search` |

## Regex Pattern

```python
re.search(r'(?:^|\s)is:(issue|pull-request)', query, re.IGNORECASE)
```

Matches `is:issue` or `is:pull-request` only when preceded by start-of-string or whitespace. Case-insensitive.
