# Step 4: Server wrapper updates + forwarding test

> **Context**: See `pr_info/steps/summary.md` for the full issue and architecture.
> **Depends on**: Steps 1–3 (read_file util is complete).

## Goal

Expose the new parameters through the MCP tool layer in `server.py` for both `read_file` and `read_reference_file`. Update the existing forwarding test.

## WHERE

- **Modify**: `src/mcp_workspace/server.py` — `read_file` and `read_reference_file` tool functions
- **Modify**: `tests/test_reference_projects.py` — update `test_read_reference_file_success`

## WHAT

### `read_file` tool (server.py)

```python
@mcp.tool()
@log_function_call
def read_file(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    with_line_numbers: Optional[bool] = None,
) -> str:
```

Forward `start_line`, `end_line`, `with_line_numbers` to `read_file_util(...)`.

### `read_reference_file` tool (server.py)

```python
@mcp.tool()
@log_function_call
def read_reference_file(
    reference_name: str,
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    with_line_numbers: Optional[bool] = None,
) -> str:
```

Forward `start_line`, `end_line`, `with_line_numbers` to `read_file_util(...)`.

## HOW

- Both wrappers pass the new params as keyword arguments to `read_file_util`.
- No validation in the wrappers — `read_file_util` handles all validation (Step 1).
- The `_check_not_gitignored` call in `read_file` stays unchanged.

## ALGORITHM

```
# In server.py read_file:
content = read_file_util(
    file_path, project_dir=_project_dir,
    start_line=start_line, end_line=end_line,
    with_line_numbers=with_line_numbers,
)

# In server.py read_reference_file:
return read_file_util(
    file_path, project_dir=ref_path,
    start_line=start_line, end_line=end_line,
    with_line_numbers=with_line_numbers,
)
```

## DATA

- Return type: `str` (unchanged for both tools).
- All new params are `Optional` with `None` defaults — backward compatible.

## Test updates

### In `tests/test_reference_projects.py`

Update `test_read_reference_file_success` — the existing `assert_called_once_with` will fail because the new kwargs are now forwarded. Update the expected call:

```python
mock_read_file.assert_called_once_with(
    "test_file.txt",
    project_dir=test_projects["test_proj"],
    start_line=None,
    end_line=None,
    with_line_numbers=None,
)
```

Add one additional test to verify params are forwarded with values:

| Test | Input | Expected |
|------|-------|----------|
| `test_read_reference_file_forwards_line_range_params` | `start_line=5, end_line=10, with_line_numbers=True` | `read_file_util` called with those kwargs |

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.
Implement Step 4: update the MCP tool wrappers in server.py (read_file and
read_reference_file) to accept and forward start_line, end_line, and
with_line_numbers to read_file_util. Update the existing forwarding test in
test_reference_projects.py and add a test that verifies non-None params are
forwarded. Run all code quality checks after.
```
