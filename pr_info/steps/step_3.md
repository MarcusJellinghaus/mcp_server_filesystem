# Step 3: `with_line_numbers` formatting

> **Context**: See `pr_info/steps/summary.md` for the full issue and architecture.
> **Depends on**: Steps 1–2 (validation and slicing are in place).

## Goal

Implement the `with_line_numbers` parameter: when resolved to `True`, prefix each returned line with a right-aligned, dynamic-width line number and `→` separator.

## WHERE

- **Modify**: `src/mcp_workspace/file_tools/file_operations.py` — `read_file` function (add formatting after slicing)
- **Modify**: `tests/file_tools/test_file_operations.py` — add formatting tests

## WHAT

After collecting the lines (from Step 2), resolve the `with_line_numbers` default and optionally apply line-number prefixes.

## HOW

- **Default resolution**: if `with_line_numbers is None`, set it to `True` when a range is given, `False` otherwise.
- **Formatting**: when `True`, compute column width from the largest line number in the slice, then prefix each line as `f"{line_num:>{width}}→{line_content}"`.
- The streaming loop from Step 2 already collects `list[tuple[int, str]]`, so the line numbers are already available — no data-shape refactor required here, just consume the existing tuples.

## ALGORITHM

```
# After collecting lines (as list of (line_num, line_content) tuples):
if with_line_numbers is None:
    with_line_numbers = (start_line is not None)
if not with_line_numbers or not collected_lines:
    return "".join(line for _, line in collected_lines)
width = len(str(collected_lines[-1][0]))
return "".join(f"{num:>{width}}→{line}" for num, line in collected_lines)
```

## DATA

- Return type: `str` (unchanged).
- Prefix format example (lines 10–12): `"10→def foo():\n11→    return 42\n12→\n"`
- Prefix format example (lines 12343–12345): `"12343→...\n12344→...\n12345→...\n"` (width 5)

## Tests to add (TDD — write these first)

| Test | Input | Expected |
|------|-------|----------|
| `test_read_file_line_numbers_default_on_for_range` | `start_line=2, end_line=3` (no explicit `with_line_numbers`) | `"2→line 2\n3→line 3\n"` |
| `test_read_file_line_numbers_default_off_for_full_read` | No params | Raw content, no prefixes |
| `test_read_file_line_numbers_explicit_false_on_range` | `start_line=2, end_line=3, with_line_numbers=False` | `"line 2\nline 3\n"` (no prefixes) |
| `test_read_file_line_numbers_explicit_true_on_full_read` | `with_line_numbers=True` | All lines prefixed |
| `test_read_file_line_numbers_dynamic_width_narrow` | Lines 1–9 | Width 1: `"1→..."` |
| `test_read_file_line_numbers_dynamic_width_wide` | Lines 99–101 of a 101+ line file | Width 3: `" 99→...\n100→...\n101→...\n"` |
| `test_read_file_slicing_start_past_eof_with_line_numbers` | `start_line=100, end_line=200, with_line_numbers=True` | `""` (moved from Step 2 because it depends on `with_line_numbers`) |

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.
Implement Step 3: add with_line_numbers formatting to `read_file` in
file_operations.py. Resolve the smart default (True for ranges, False for full
reads), then apply dynamic-width "N→content" prefixes when enabled.
Write the tests first (TDD), then the implementation. Run all code quality checks after.
```
