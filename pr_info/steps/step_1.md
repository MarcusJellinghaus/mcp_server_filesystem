# Step 1: Core Fallback Logic + Tests

**Ref:** See `pr_info/steps/summary.md` for full context (Issue #139)

## LLM Prompt

> Implement step 1 of the plan in `pr_info/steps/summary.md`.
> Read `pr_info/steps/step_1.md` for detailed instructions.
> Read all files listed in WHERE before making changes.
> Follow TDD: update tests first, then implement, then run all checks.

## WHERE

- `tests/file_tools/test_search.py` — replace existing test, add new tests
- `src/mcp_workspace/file_tools/search.py` — fallback logic + docstring

## WHAT

### Tests to replace/add in `tests/file_tools/test_search.py`

**Remove:** `test_search_files_invalid_regex_raises` (in `TestSearchFilesContentSearch`)

**Add** (in `TestSearchFilesContentSearch`):

1. `test_search_files_invalid_regex_falls_back_to_literal(self, project_dir)` — verifies fallback works and `"note"` is present
2. `test_search_files_valid_regex_no_note(self, project_dir)` — verifies valid regex does NOT produce a `"note"` field

### Implementation change in `search_files()` in `search.py`

Change the `try/except re.error` block to fallback instead of raise.

## HOW

No new imports, decorators, or integration points needed. `re.escape` is already available from the `re` import.

## ALGORITHM (search.py, inside `search_files()`)

```
try:
    compiled = re.compile(pattern)
    note = None
except re.error:
    compiled = re.compile(re.escape(pattern))
    note = "Pattern treated as literal text (invalid regex). Use Python re syntax for regex search."

result = _search_content(...)

if note is not None:
    result["note"] = note

return result
```

## DATA

Result dict gains an optional `"note"` key (str), only present when fallback triggers:

```python
{
    "mode": "content_search",
    "details": [...],
    "total_matches": 2,
    "truncated": False,
    "note": "Pattern treated as literal text (invalid regex). Use Python re syntax for regex search."
}
```

### Docstring update for `search_files()` in `search.py`

Change the `pattern` parameter description from:
```
pattern: Regex pattern for content searching.
```
to:
```
pattern: Python regex to match file contents. Invalid regex patterns
    are automatically treated as literal text.
    (e.g. "def foo", "TODO.*fix")
```

Remove from Raises section: `pattern is an invalid regex.`

## TEST DETAILS

### Test 1: `test_search_files_invalid_regex_falls_back_to_literal`

```python
def test_search_files_invalid_regex_falls_back_to_literal(self, project_dir):
    """Invalid regex pattern falls back to literal search with note."""
    (project_dir / "code.py").write_text("def hello(world):\n    pass\n")
    result = search_files(project_dir, pattern="hello(")
    assert result["mode"] == "content_search"
    assert result["total_matches"] == 1
    assert "hello(" in result["details"][0]["text"]
    assert "note" in result
    assert "literal" in result["note"].lower()
```

### Test 2: `test_search_files_valid_regex_no_note`

```python
def test_search_files_valid_regex_no_note(self, project_dir):
    """Valid regex pattern does not produce a note field."""
    (project_dir / "code.py").write_text("def hello():\n    pass\n")
    result = search_files(project_dir, pattern=r"def \w+")
    assert result["mode"] == "content_search"
    assert "note" not in result
```
