# Step 1: Parameter validation in `read_file`

> **Context**: See `pr_info/steps/summary.md` for the full issue and architecture.

## Goal

Add the three new optional parameters to `read_file` and implement strict input validation. Existing behavior must remain unchanged when no new params are passed.

## WHERE

- **Modify**: `src/mcp_workspace/file_tools/file_operations.py` — `read_file` function
- **Modify**: `tests/file_tools/test_file_operations.py` — add validation tests

## WHAT

- Add the three new optional parameters to the `read_file` signature.
- Implement strict input validation that raises `ValueError` for invalid combinations.
- Update the `read_file` docstring to document the new params (`start_line`, `end_line`, `with_line_numbers`) and the `Raises ValueError` cases.

### Modified function signature

```python
def read_file(
    file_path: str,
    project_dir: Path,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    with_line_numbers: Optional[bool] = None,
) -> str:
```

### Validation rules (raise `ValueError`)

- `start_line` or `end_line` is not `None` and not an `int`
- `start_line` or `end_line` < 1
- Exactly one of `start_line` / `end_line` is provided (both or neither)
- `end_line < start_line`
- Booleans: `True` (=1) is valid; `False` (=0) fails the `>= 1` check. No special-case rejection.

## HOW

- Add validation block after existing parameter checks, before the file-open logic.
- No changes to the file-reading logic yet — this step only validates, then falls through to existing `f.read()`.
- No changes to imports beyond adding `Optional` if not already imported (it is already imported).

## ALGORITHM

```
if only one of (start_line, end_line) is provided:
    raise ValueError
if start_line is not None:
    if not isinstance(start_line, int) or not isinstance(end_line, int):
        raise ValueError
    if start_line < 1 or end_line < 1:
        raise ValueError
    if end_line < start_line:
        raise ValueError
```

## DATA

- No change to return type (`str`).
- `ValueError` messages should be descriptive (e.g., "start_line and end_line must both be provided or both omitted").

## Tests to add (TDD — write these first)

All tests use a simple test file created via the `project_dir` fixture.

| Test | Input | Expected |
|------|-------|----------|
| `test_read_file_rejects_one_sided_range_start_only` | `start_line=1, end_line=None` | `ValueError` |
| `test_read_file_rejects_one_sided_range_end_only` | `start_line=None, end_line=5` | `ValueError` |
| `test_read_file_rejects_zero_start_line` | `start_line=0, end_line=5` | `ValueError` |
| `test_read_file_rejects_zero_end_line` | `start_line=1, end_line=0` | `ValueError` |
| `test_read_file_rejects_negative_start_line` | `start_line=-1, end_line=5` | `ValueError` |
| `test_read_file_rejects_negative_end_line` | `start_line=1, end_line=-1` | `ValueError` |
| `test_read_file_rejects_end_before_start` | `start_line=5, end_line=3` | `ValueError` |
| `test_read_file_rejects_non_int_start_line` | `start_line="1", end_line=5` | `ValueError` |
| `test_read_file_rejects_non_int_end_line` | `start_line=1, end_line=2.5` | `ValueError` |
| `test_read_file_accepts_bool_true_as_line_1` | `start_line=True, end_line=True` | No error (reads line 1) |
| `test_read_file_rejects_bool_false_as_zero` | `start_line=False, end_line=5` | `ValueError` (0 < 1) |
| `test_read_file_unchanged_without_new_params` | No new params | Returns full content unchanged |

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.
Implement Step 1: add the three new optional parameters to `read_file` in
`src/mcp_workspace/file_tools/file_operations.py` and implement input validation
(raise ValueError for invalid inputs). Do NOT implement slicing or line-number
formatting yet — just validation. Write the tests first (TDD), then the implementation.
Run all code quality checks after.
```
