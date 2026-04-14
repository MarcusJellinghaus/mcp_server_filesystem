# Step 3: Normalize CRLF in `edit_file`

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## Goal

Normalize line endings in `edit_file` for both file content (handles CRLF files on Linux/Mac) and LLM-provided `old_text`/`new_text` (handles CRLF from LLM input).

## WHERE

- `src/mcp_workspace/file_tools/edit_file.py` — modify `edit_file` function
- `tests/file_tools/test_edit_file.py` — add CRLF tests

## WHAT

Three normalization points inside the existing `edit_file` function:

1. Normalize `original_content` after reading (line ~69)
2. Normalize `old_text` per edit (line ~103)
3. Normalize `new_text` per edit (line ~104)

## HOW

`normalize_line_endings` is already imported from `path_utils` (done in Step 1).

Add three lines in `edit_file`:

```python
# After line 69: original_content = f.read()
original_content = normalize_line_endings(original_content)

# After line 103-104: old_text = edit["old_text"] / new_text = edit["new_text"]
old_text = normalize_line_endings(old_text)
new_text = normalize_line_endings(new_text)
```

## ALGORITHM

```
original_content = read file
original_content = normalize_line_endings(original_content)  # NEW
...
for each edit:
    old_text = normalize_line_endings(edit["old_text"])       # NEW
    new_text = normalize_line_endings(edit["new_text"])       # NEW
    # ... existing match + replace logic unchanged ...
```

## DATA

- **Input**: file with CRLF on disk; `old_text`/`new_text` with `\r\n` from LLM
- **Output**: successful match; file written with clean `\n` content (Python text-mode handles OS convention)

## Tests (TDD — write first)

In `tests/file_tools/test_edit_file.py`:

1. **`test_edit_file_crlf_old_text_matches`**: Create file with `"hello\nworld\n"`. Call `edit_file` with `old_text="hello\r\nworld\r\n"`, `new_text="hi\nworld\n"`. Verify success — CRLF in `old_text` should match LF in file.
2. **`test_edit_file_crlf_new_text_no_contamination`**: Create file with `"aaa\nbbb\n"`. Call `edit_file` with `old_text="aaa"`, `new_text="ccc\r\n"`. Read back raw bytes and verify no `\r\n` contamination (or only platform-appropriate endings).
3. **`test_edit_file_crlf_file_content_normalized`**: Write a file with raw `\r\n` bytes (`open("wb")`). Call `edit_file` with LF `old_text` matching content. Verify success — CRLF file content should be normalized before matching.

## Commit

`fix: normalize CRLF in edit_file`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for context.

Implement Step 3: Normalize CRLF line endings in edit_file.

1. In src/mcp_workspace/file_tools/edit_file.py:
   - After reading original_content (~line 69), add: original_content = normalize_line_endings(original_content)
   - After extracting old_text and new_text per edit (~lines 103-104), add normalization for both
2. In tests/file_tools/test_edit_file.py:
   - Add test_edit_file_crlf_old_text_matches — CRLF old_text matches LF file
   - Add test_edit_file_crlf_new_text_no_contamination — CRLF new_text doesn't leak to disk
   - Add test_edit_file_crlf_file_content_normalized — CRLF file matched by LF old_text

Run all three quality checks (pylint, pytest, mypy) and fix any issues before committing.
```
