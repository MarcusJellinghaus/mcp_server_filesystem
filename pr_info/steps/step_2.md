# Step 2: Normalize CRLF in `save_file` / `append_file`

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## Goal

Normalize LLM content at the write boundary in `file_operations.py`. Refactor `append_file` to use `_validate_save_parameters` to eliminate duplicated validation.

## WHERE

- `src/mcp_workspace/file_tools/file_operations.py` — modify `_validate_save_parameters`, refactor `append_file`
- `tests/file_tools/test_file_operations.py` — add CRLF tests

## WHAT

### Modified: `_validate_save_parameters` (line ~165)

Add normalization of `content` before returning:

```python
def _validate_save_parameters(
    file_path: str, content: Any, project_dir: Path
) -> tuple[Path, str, str]:
```

### Refactored: `append_file`

Replace duplicated validation (lines 304-322) with a call to `_validate_save_parameters`.

## HOW

- In `file_operations.py`: add `from mcp_workspace.file_tools.path_utils import normalize_line_endings` to the existing `path_utils` import
- In `_validate_save_parameters`: add `content = normalize_line_endings(content)` before the `return` statement (line 166)
- In `append_file`: replace the duplicated validation block with `abs_path, rel_path, validated_content = _validate_save_parameters(file_path, content, project_dir)`, then use `validated_content` (normalized) for concatenation

## ALGORITHM

### `_validate_save_parameters` change
```
# ... existing validation ...
content = normalize_line_endings(content)  # NEW: normalize before return
return abs_path, rel_path, content
```

### `append_file` refactored
```
abs_path, rel_path, validated_content = _validate_save_parameters(file_path, content, project_dir)
assert file exists and is_file (keep existing checks using abs_path)
existing_content = read_file(file_path, project_dir)
combined_content = existing_content + validated_content
return save_file(file_path, combined_content, project_dir)
```

Note: `save_file` calls `_validate_save_parameters` again on `combined_content`, but `normalize_line_endings` is idempotent so this is harmless and keeps the API contract simple.

## DATA

- **Input**: `content` with `\r\n` or `\r`
- **Output**: file on disk with clean `\n` (Python text-mode handles OS convention)

## Tests (TDD — write first)

In `tests/file_tools/test_file_operations.py`:

1. **`test_save_file_normalizes_crlf`**: Call `save_file` with `"line1\r\nline2\r\n"`. Read back with `open(path, 'rb')` and verify no `\r\r\n` (double carriage return) exists in the raw bytes. This is the key assertion — on any platform, `\r\r\n` means the normalization failed.
2. **`test_append_file_normalizes_crlf`**: Create file with `"existing\n"`, append `"new\r\nline\r\n"`. Read back with `open(path, 'rb')` and verify no `\r\r\n` (double carriage return) exists in the raw bytes. This is the key assertion — on any platform, `\r\r\n` means the normalization failed.
3. **`test_append_file_validation_via_validate_save_parameters`**: Verify `append_file` still raises `ValueError` for invalid content type (confirms refactor didn't break validation).

## Commit

`fix: normalize CRLF in save_file/append_file`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.

Implement Step 2: Normalize CRLF line endings in save_file and append_file.

1. In src/mcp_workspace/file_tools/file_operations.py:
   - Import normalize_line_endings from path_utils
   - Add content = normalize_line_endings(content) in _validate_save_parameters before the return
   - Refactor append_file to use _validate_save_parameters instead of duplicating validation
2. In tests/file_tools/test_file_operations.py:
   - Add test_save_file_normalizes_crlf
   - Add test_append_file_normalizes_crlf
   - Add test confirming append_file validation still works after refactor

Run all three quality checks (pylint, pytest, mypy) and fix any issues before committing.
```
