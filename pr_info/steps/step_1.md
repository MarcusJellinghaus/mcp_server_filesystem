# Step 1: Rewrite Utility Function and Its Tests

## Context

Read `pr_info/steps/summary.md` for the full picture. This step rewrites the core
`edit_file` utility in `src/mcp_workspace/file_tools/edit_file.py` and its primary
test file `tests/file_tools/test_edit_file.py`.

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file.
> Rewrite `src/mcp_workspace/file_tools/edit_file.py` with the new signature and
> rewrite `tests/file_tools/test_edit_file.py` to test the new interface (TDD: write
> tests first, then make them pass). Run all quality checks after. Commit as one unit.

## WHERE

- `src/mcp_workspace/file_tools/edit_file.py` — utility function
- `tests/file_tools/test_edit_file.py` — primary tests

## WHAT — New utility function signature

```python
def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
    project_dir: Optional[Path] = None,
) -> str:
```

## HOW — Integration points

- Imports stay the same: `normalize_line_endings`, `normalize_path` from `path_utils`
- `__init__.py` re-export works unchanged (same function name)
- Server layer is updated in step 2 (will fail until then — that's OK)

## ALGORITHM — Core logic (utility function)

```
resolve file_path, read content, normalize line endings
if old_string is empty → prepend new_string, write, return diff
if old_string in content:
    if count > 1 and not replace_all → raise ValueError("multiple matches")
    position-aware already-applied check → return message if matched
    replace old_string with new_string (once or all based on replace_all)
    write file, return diff string
else:
    contextual already-applied check → return message if matched
    raise ValueError (with backslash hint if applicable)
```

## ALGORITHM — Already-applied detection

```
# Position-aware check (when old_string IS found but edit is already applied):
if len(new_string) > len(old_string):
    pos = content.find(old_string)
    if content[pos:pos+len(new_string)] == new_string → return "No changes needed" message

# Contextual check (when old_string is NOT found):
if old_string not in content and new_string in content → return "No changes needed" message
```

## DATA — Return values

- **Success**: diff string from `_create_diff(original, modified, filename)`
- **Already applied**: `"No changes needed - edit already applied"`
- **Failure**: raises `ValueError` (text not found, multiple matches) or `FileNotFoundError`

## WHAT — Functions to keep

- `_create_diff(original, modified, filename) -> str` — unchanged
- `_truncate(text, max_len=50) -> str` — unchanged
- `_is_edit_already_applied(content, old_text, new_text) -> bool` — unchanged

## WHAT — Functions to remove

- `_error_result` — no longer returning error dicts
- `_preserve_basic_indentation` — dead code
- `create_unified_diff` (public alias) — only used in one test, remove

## WHAT — Tests to write (test_edit_file.py)

Rewrite the file with these test cases:

1. **Basic replacement** — replaces first occurrence, returns diff string
2. **With project_dir** — relative path resolution works
3. **File not found** — raises `FileNotFoundError`
4. **Text not found** — raises `ValueError`
5. **Already applied (contextual)** — apply edit, re-apply → returns message string
6. **Already applied (position-aware)** — old_string is prefix of new_string, content already has new_string → returns message
7. **Empty old_string** — inserts new_string at beginning of file
8. **replace_all=True** — replaces all occurrences
9. **Multiple matches without replace_all** — raises `ValueError`
10. **Large block replacement** — multi-line edit works
11. **Mixed indentation** — tabs and spaces preserved correctly
12. **CRLF normalization** — CRLF in old_string/new_string/file content handled
13. **Backslash hint** — single backslash old_string triggers hint in ValueError message
14. **Delete text (empty new_string)** — replaces old_string with empty string, removing it from the file

## Decisions

- Tests use `unittest.TestCase` style (matches existing pattern in this file)
- Tests use `tempfile.TemporaryDirectory` for isolation (matches existing pattern)
- No `dry_run` tests — feature removed
- No `preserve_indentation` tests — feature removed
- No batch edit tests — feature removed
