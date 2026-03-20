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

> **Decision 1:** Also update `.absolute()` → `.resolve()` in expected values across ALL test classes (not just integration tests). This includes `test_auto_rename_duplicates` expected dict values and any other `.absolute()` usage in the file.

### 1b. Update ALL `.absolute()` → `.resolve()` in test assertions

Update **every** `.absolute()` call in the test file to `.resolve()`. This includes:

- `TestReferenceProjectIntegration`: the three `test_main_*` methods that assert `project_dir` and `expected_ref_projects`
- `TestReferenceProjectCLI.test_auto_rename_duplicates`: expected dict values use `.absolute()`
- Any other `.absolute()` usage in the file (e.g., `TestReferenceProjectMCPTools`, `TestReferenceProjectServerStorage`)

```python
# Old
assert call_args[0][0] == Path("/test/project").absolute()
# New
assert call_args[0][0] == Path("/test/project").resolve()
```

> **Decision 1:** Comprehensive update across entire test file, not just integration tests.

### 1c. Add parameterized overlap test using real temp directories

Add a single parameterized test to `TestReferenceProjectCLI` using the `tmp_path` fixture to create real directories.

> **Decision 2:** Use real temp directories instead of mocking `Path.resolve`. This avoids fragile global mocking.

**Function signature:**
```python
@pytest.mark.parametrize(
    "ref_subpath, project_subpath, expected_count, expected_warning_fragment",
    [
        ("main", "main", 0, "same directory"),
        ("main/sub", "main", 0, "subdirectory of the main project"),
        ("projects", "projects/main", 0, "parent of the main project"),
        ("other", "main", 1, None),
    ],
)
def test_overlap_detection(self, tmp_path, ref_subpath, project_subpath, expected_count, expected_warning_fragment):
```

**Pseudocode:**
```
# Create real directories under tmp_path
ref_dir = tmp_path / ref_subpath
ref_dir.mkdir(parents=True, exist_ok=True)
project_dir = tmp_path / project_subpath
project_dir.mkdir(parents=True, exist_ok=True)

# No mocking of Path.resolve needed — real paths resolve correctly
with patch("mcp_workspace.main.stdlogger") as mock_logger:
    result = validate_reference_projects([f"ref={ref_dir}"], project_dir=project_dir)
    assert len(result) == expected_count
    if expected_warning_fragment:
        assert any(expected_warning_fragment in str(call) for call in mock_logger.warning.call_args_list)
```

### 1d. Strengthen `test_path_normalization` assertion

> **Decision 5:** Assert the result equals `Path("./relative/path").resolve()` explicitly, not just `is_absolute()`.

```python
# Old
assert result["proj"].is_absolute()
# New
assert result["proj"] == Path("./relative/path").resolve()
```

## HOW

- Import `pytest` (already imported)
- Use `@patch("mcp_workspace.main.Path.exists")` and `@patch("mcp_workspace.main.Path.is_dir")` as existing tests do
- Use `@patch("mcp_workspace.main.stdlogger")` to capture warnings
- For overlap tests: use `tmp_path` fixture with real directories (no mocking of `Path.resolve`)

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
