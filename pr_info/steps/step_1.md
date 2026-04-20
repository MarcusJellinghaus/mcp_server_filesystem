# Step 1: Add tests and tighten content type hint from Any to str

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: Add tests that verify `save_file` and `append_file` reject non-string content, then change the `content` parameter type hint from `Any` to `str` in both functions in `server.py`. Keep existing runtime `isinstance` and `None` checks as defense-in-depth. Run all code quality checks (pylint, mypy, pytest) and fix any issues.

## WHERE

- `tests/test_server.py` — add test functions
- `src/mcp_workspace/server.py` — modify function signatures

## WHAT

### Tests to add in `tests/test_server.py`

```python
def test_save_file_rejects_non_string_content(project_dir: Path) -> None:
    """save_file rejects dict content with TypeError/ValueError."""
    ...

def test_append_file_rejects_non_string_content(project_dir: Path) -> None:
    """append_file rejects dict content with TypeError/ValueError."""
    ...
```

### Production changes in `src/mcp_workspace/server.py`

| Function | Current signature | New signature |
|----------|------------------|---------------|
| `save_file` | `content: Any` | `content: str` |
| `append_file` | `content: Any` | `content: str` |

## HOW

- Change the type annotation on line ~168 (`save_file`) and line ~195 (`append_file`)
- Keep the `if content is None` and `elif not isinstance(content, str)` runtime checks unchanged (defense-in-depth)
- Check if `Any` is still used elsewhere in imports — it is (return types of `search_files`, `edit_file`), so keep the import

## ALGORITHM

```
1. Add two test functions that call save_file/append_file with dict content
2. Assert they raise an error (ValueError or TypeError depending on call path)
3. In server.py, change `content: Any` to `content: str` on both functions
4. Verify import of `Any` is still needed (yes — used by other functions)
5. Run pylint, mypy, pytest — all must pass
```

## DATA

- No new data structures or return values
- Existing return types unchanged (`bool` for both functions)

## Commit message

```
fix: tighten content type hint from Any to str in save_file and append_file (#20)
```
