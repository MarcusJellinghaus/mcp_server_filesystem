# Step 1: Add `normalize_line_endings` to `path_utils.py`

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## Goal

Establish the shared `normalize_line_endings` function in `path_utils.py` and wire up `edit_file.py` to use it instead of its local legacy copy.

## WHERE

- `src/mcp_workspace/file_tools/path_utils.py` — add function
- `src/mcp_workspace/file_tools/edit_file.py` — remove local copy, import from `path_utils`
- `tests/file_tools/test_edit_file.py` — update import, add standalone `\r` test

## WHAT

### Function signature (in `path_utils.py`)

```python
def normalize_line_endings(text: str) -> str:
    """Convert all line endings to Unix style (\n)."""
```

## HOW

- Add the function to `path_utils.py` (after existing `normalize_path`)
- In `edit_file.py`: remove the legacy `normalize_line_endings` function (~line 258), keep `create_unified_diff` re-export unchanged
- In `edit_file.py`: add `normalize_line_endings` to the existing `from mcp_workspace.file_tools.path_utils import normalize_path` import
- In `test_edit_file.py`: the import `from mcp_workspace.file_tools.edit_file import normalize_line_endings` — keep it working by re-exporting from `edit_file.py` OR update the import. Simplest: re-export in `edit_file.py` via the updated import line.

## ALGORITHM

```
def normalize_line_endings(text):
    text = text.replace('\r\n', '\n')   # CRLF → LF (must be first)
    text = text.replace('\r', '\n')     # standalone CR → LF
    return text
```

Order matters: `\r\n` first to avoid splitting into `\n\n`.

## DATA

- **Input**: `str` with arbitrary line endings
- **Output**: `str` with only `\n` line endings

## Tests (TDD — write first)

In `tests/file_tools/test_edit_file.py`, update the existing `test_normalize_line_endings` and add a standalone `\r` case:

1. **Existing test** (`test_normalize_line_endings`): already tests `\r\n` → `\n`. Ensure it still passes with the new import path.
2. **New test**: `normalize_line_endings("line1\rline2\rline3")` → `"line1\nline2\nline3"`
3. **New test**: mixed endings `"a\r\nb\rc\n"` → `"a\nb\nc\n"`

## Commit

`feat: add normalize_line_endings to path_utils`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Implement Step 1: Move normalize_line_endings to path_utils.py as the shared utility.

1. Add normalize_line_endings to src/mcp_workspace/file_tools/path_utils.py — handles \r\n and standalone \r
2. In src/mcp_workspace/file_tools/edit_file.py — remove the local legacy copy, import from path_utils instead (keep it re-exported so existing test imports work)
3. In tests/file_tools/test_edit_file.py — add test for standalone \r and mixed line endings

Run all three quality checks (pylint, pytest, mypy) and fix any issues before committing.
```
