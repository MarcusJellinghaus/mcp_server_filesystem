# Step 2: Line-range slicing with streaming

> **Context**: See `pr_info/steps/summary.md` for the full issue and architecture.
> **Depends on**: Step 1 (validation is already in place).

## Goal

Replace `f.read()` with line-by-line streaming using `enumerate(file)`. When `start_line` / `end_line` are provided, return only the requested lines. This step does NOT add line-number prefixes — that's Step 3.

## WHERE

- **Modify**: `src/mcp_workspace/file_tools/file_operations.py` — `read_file` function (replace the read logic)
- **Modify**: `tests/file_tools/test_file_operations.py` — add slicing tests

## WHAT

Replace the file-reading block inside `read_file`:

```python
# OLD: content = file_handle.read()
# NEW: stream line-by-line, collect requested range
```

## HOW

- Use `enumerate(file_handle, start=1)` to iterate with 1-based line numbers.
- Collect `(line_num, line)` tuples directly (not just lines). This avoids a refactor in Step 3, which needs the line numbers anyway.
- When no range is given (`start_line is None`): collect all `(line_num, line)` tuples, join, return (functionally identical to `f.read()`).
- When a range is given: collect tuples where `start_line <= line_num <= end_line`, break after `end_line`.
- Clamping: if `end_line` exceeds file length, just return what's available.
- Past-EOF: if `start_line` > total lines, return `""`.
- **Logging**: replace the existing `"Successfully read %s bytes"` log line. When slicing is active, log the `start_line`/`end_line` range instead. No byte count is included in the slicing path going forward (use your judgment whether to keep a simpler log for the non-slicing path or unify — but no byte counts).

## ALGORITHM

```
collected: list[tuple[int, str]] = []
for line_num, line in enumerate(file_handle, start=1):
    if start_line is None or (start_line <= line_num <= end_line):
        collected.append((line_num, line))
    if end_line is not None and line_num >= end_line:
        break
return "".join(line for _, line in collected)
```

## DATA

- Return type: `str` (unchanged).
- Full reads return identical content to the previous `f.read()` approach.
- Sliced reads return the raw lines without any prefix formatting.

## Tests to add (TDD — write these first)

Create a multiline test file (e.g., 10 lines: `"line 1\nline 2\n...\nline 10\n"`).

| Test | Input | Expected |
|------|-------|----------|
| `test_read_file_slicing_basic` | `start_line=3, end_line=5` | `"line 3\nline 4\nline 5\n"` |
| `test_read_file_slicing_single_line` | `start_line=1, end_line=1` | `"line 1\n"` |
| `test_read_file_slicing_clamp_past_eof` | `start_line=8, end_line=20` | `"line 8\nline 9\nline 10\n"` |
| `test_read_file_slicing_start_past_eof` | `start_line=100, end_line=200` | `""` |
| `test_read_file_slicing_exact_eof` | 10-line file, `start_line=10, end_line=10` | `"line 10\n"` (most common off-by-one location) |
| `test_read_file_full_read_unchanged` | No new params | Full content identical to direct file read |
| `test_read_file_no_trailing_newline` | File ends without `\n`, slice last line | Last line has no `\n` |
| `test_read_file_slicing_large_file` | 10000-line file, `start_line=5000, end_line=5002` | (a) returned content equals exactly the 3 expected lines and (b) the function returns promptly without loading the entire file via `f.read()` (verified by streaming behavior — do not assert "only N lines read") |

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.
Implement Step 2: replace f.read() in `read_file` with line-by-line streaming
using enumerate(file). When start_line/end_line are provided, return only the
requested lines. Handle EOF clamping and past-EOF empty returns.
Do NOT implement line-number formatting yet.
Write the tests first (TDD), then the implementation. Run all code quality checks after.
```
