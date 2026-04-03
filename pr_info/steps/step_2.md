# Step 2: Content Search and Combined Mode

> **Context**: See [summary.md](summary.md) for overall design. This is step 2 of 3. Step 1 established the `search_files` function with glob-only mode.

## LLM Prompt

Add content search (regex) and combined (glob + regex) modes to `search_files` in `src/mcp_workspace/file_tools/search.py`. Follow TDD — write tests first, then implement. Read `summary.md` for architecture. Run all quality checks after.

## WHERE

- **Modify**: `src/mcp_workspace/file_tools/search.py`
- **Modify**: `tests/file_tools/test_search.py`

## WHAT

Extend `search_files()` to handle:
- **Content search** (`pattern` only): search all files with regex
- **Combined** (`glob` + `pattern`): search within glob-matched files
- **`context_lines`**: include surrounding lines around matches
- **`max_result_lines`**: hard cap on total output lines (dual cap with `max_results`)
- **Binary file skipping**: catch `UnicodeDecodeError`, skip silently
- **Regex validation**: `re.compile()` upfront, raise `ValueError` on bad pattern

## HOW

- Read files using `open(abs_path, "r", encoding="utf-8")` directly (not `read_file` util — we need line-by-line access and must skip binary files silently instead of raising)
- Use `normalize_path` to resolve file paths to absolute
- Use `re.compile(pattern)` for upfront validation and matching
- `context_lines` extracts surrounding lines as flat `\n`-joined text

## ALGORITHM (content search)

```
1. compiled = re.compile(pattern)  # raises re.error → wrap as ValueError
2. files = list_files(...) filtered by glob (if provided)
3. For each file: open UTF-8, skip on UnicodeDecodeError
4.   For each line: if compiled.search(line), extract context window, append match
5.   Check dual cap: break if max_results or max_result_lines reached
6. Return {"mode": "content_search", "matches": [...], "total_matches": N, "truncated": bool}
```

## DATA

### Return value (content search mode)
```python
{
    "mode": "content_search",
    "matches": [
        {"file": "src/server.py", "line": 42, "text": "def foo(bar):"},
        {"file": "tests/test_server.py", "line": 18, "text": "    result = foo(123)"},
    ],
    "total_matches": 2,
    "truncated": False
}
```

### With `context_lines > 0`
```python
{"file": "src/server.py", "line": 42, "text": "# comment above\ndef foo(bar):\n    pass"}
```

The `line` field still points to the match line. `text` contains surrounding lines joined by `\n`.

## TESTS (additions to `tests/file_tools/test_search.py`)

1. `test_search_files_pattern_finds_content` — create files with known content, regex matches correct lines
2. `test_search_files_pattern_no_matches` — regex that matches nothing → empty `matches` list
3. `test_search_files_invalid_regex_raises` — bad regex pattern → `ValueError`
4. `test_search_files_combined_mode` — glob + pattern filters both file paths and content
5. `test_search_files_context_lines` — verify surrounding lines included in `text` field
6. `test_search_files_max_result_lines_truncation` — verify `max_result_lines` cap triggers `truncated: True`
7. `test_search_files_skips_binary_files` — create a file with non-UTF-8 bytes, verify it's skipped without error

## COMMIT

```
feat: add search_files content and combined search modes
```
