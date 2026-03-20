# Step 1: Update Tests (TDD — Tests First)

> **Context**: See `pr_info/steps/summary.md` for full issue summary.
> This step writes all tests before any production code changes.

## WHERE

- `tests/test_reference_projects.py`

## WHAT

### 1a. Update existing `validate_reference_projects()` calls

Every existing call to `validate_reference_projects()` must add `project_dir=Path("/unrelated/project")` — a non-overlapping path so existing behavior is unchanged.

**Affected call sites** (search for `validate_reference_projects(` in the test file):

- `TestReferenceProjectCLI.test_auto_rename_duplicates`
- `TestReferenceProjectCLI.test_invalid_format_warnings`
- `TestReferenceProjectCLI.test_path_normalization`
- `TestReferenceProjectCLI.test_nonexistent_path_warning`
- `TestReferenceProjectServerStorage.test_empty_name_validation`

Each call changes from:
```python
result = validate_reference_projects(reference_args)
```
to:
```python
result = validate_reference_projects(reference_args, project_dir=Path("/unrelated/project"))
```

### 1b. Update integration test assertions

In `TestReferenceProjectIntegration`, the three `test_main_*` methods assert `project_dir` using `.absolute()`. Since production code will switch to `.resolve()`, update these assertions:

```python
# Old
assert call_args[0][0] == Path("/test/project").absolute()
# New
assert call_args[0][0] == Path("/test/project").resolve()
```

Similarly update `expected_ref_projects` paths from `.absolute()` to `.resolve()`.

### 1c. Add parameterized overlap test

Add a single parameterized test to `TestReferenceProjectCLI`:

**Function signature:**
```python
@pytest.mark.parametrize(
    "ref_path_str, project_dir_str, expected_count, expected_warning_fragment",
    [
        ("/projects/main", "/projects/main", 0, "same directory"),
        ("/projects/main/sub", "/projects/main", 0, "subdirectory of the main project"),
        ("/projects", "/projects/main", 0, "parent of the main project"),
        ("/projects/other", "/projects/main", 1, None),
    ],
)
def test_overlap_detection(self, ref_path_str, project_dir_str, expected_count, expected_warning_fragment):
```

**Pseudocode:**
```
mock Path.exists → True
mock Path.is_dir → True
mock Path.resolve → return self (identity, so test paths stay as-is)
call validate_reference_projects(["ref=" + ref_path_str], project_dir=Path(project_dir_str))
assert len(result) == expected_count
if expected_warning_fragment:
    assert warning_fragment in logger warning call
```

## HOW

- Import `pytest` (already imported)
- Use `@patch("mcp_workspace.main.Path.exists")` and `@patch("mcp_workspace.main.Path.is_dir")` as existing tests do
- Use `@patch("mcp_workspace.main.stdlogger")` to capture warnings
- Mock `Path.resolve` to return the path unchanged (so test paths like `/projects/main` are used as-is for comparison)

## DATA

- `validate_reference_projects()` returns `Dict[str, Path]`
- `expected_count`: 0 for overlap cases (filtered out), 1 for non-overlap (kept)
- Warning messages checked via `mock_logger.warning.call_args_list`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.
Implement Step 1: update tests in tests/test_reference_projects.py.
- Add project_dir=Path("/unrelated/project") to all existing validate_reference_projects() calls
- Update .absolute() → .resolve() in integration test assertions
- Add the parameterized overlap detection test
Do NOT modify src/mcp_workspace/main.py yet. Tests are expected to fail at this point.
Run pylint and mypy checks after editing. Do not run pytest (tests will fail until Step 2).
```
