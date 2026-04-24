# Step 1: Harden normalize_path against OSError bypass

> **Context:** See [summary.md](summary.md) for issue overview. This is the only step.

## LLM Prompt

```
Implement the fix for issue #152. Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

1. Add two tests to tests/file_tools/test_path_utils.py (TDD — tests first)
2. Fix the except block in src/mcp_workspace/file_tools/path_utils.py
3. Run all three quality checks (pylint, pytest, mypy) and fix any issues
4. Commit: "fix: harden normalize_path against OSError bypass (#152)"
```

## WHERE

- `tests/file_tools/test_path_utils.py` — add 2 test functions
- `src/mcp_workspace/file_tools/path_utils.py` — modify `except` block (lines 65-67)

## WHAT

### Tests (add to `tests/file_tools/test_path_utils.py`)

```python
def test_normalize_path_oserror_with_traversal_rejected() -> None:
    """When resolve() raises OSError, paths with '..' are rejected."""

def test_normalize_path_oserror_clean_path_passes() -> None:
    """When resolve() raises OSError, clean relative paths pass through."""
```

### Production fix (modify `src/mcp_workspace/file_tools/path_utils.py`)

Replace the `except` block at lines 65-67.

## HOW

- Tests mock `Path.resolve` to raise `OSError` using `unittest.mock.patch.object`
- Mocking `Path.resolve` globally is safe: `absolute_path.resolve()` (line 55) is called first, so the OSError is caught before `project_dir.resolve()` (line 56) is reached
- Add `from unittest.mock import patch` to the test file imports (not currently imported)
- Tests import `normalize_path` from `mcp_workspace.file_tools.path_utils` (already imported in test file)
- For `project_dir` in mock tests, use `tmp_path` fixture or a hardcoded `Path("/fake/project")` — since `resolve()` is mocked, filesystem access doesn't matter
- When asserting the returned relative path, compare using `Path` objects to avoid platform-specific separator issues (e.g., `Path(rel_path) == Path("subdir/file.txt")`)
- Production code already has `logger = logging.getLogger(__name__)` — no new imports needed

## ALGORITHM

### Test 1 — traversal rejected:
```
mock Path.resolve to raise OSError
call normalize_path("../etc/passwd", project_dir)
assert raises ValueError with "Security error"
```

### Test 2 — clean path passes:
```
mock Path.resolve to raise OSError
call normalize_path("subdir/file.txt", project_dir)
assert returns (project_dir / "subdir/file.txt", "subdir/file.txt")
```

### Production fix:
```
except OSError:
    log warning with absolute_path
    if ".." in absolute_path.parts:
        raise ValueError (security error, path traversal)
```

## DATA

- `normalize_path()` return type unchanged: `tuple[Path, str]`
- New `ValueError` message: `f"Security error: Path '{path}' contains '..' traversal."`
- Warning log: `"Path.resolve() failed for '%s', using fallback check"`
