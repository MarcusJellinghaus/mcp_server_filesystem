# Step 1: Add `is_path_in_git_dir()` Helper and DRY-Refactor `_discover_files()`

> **Context:** See `pr_info/steps/summary.md` for the full plan. This is step 1 of 3.

## Goal

Extract a shared `is_path_in_git_dir()` helper and use it in both the existing `_discover_files()` function (replacing its inline `.git` check) and in the upcoming `is_path_gitignored()` (step 2).

## WHERE

| File | Action |
|------|--------|
| `src/mcp_workspace/file_tools/directory_utils.py` | Add function, refactor `_discover_files()` |
| `tests/file_tools/test_directory_utils.py` | Add tests for new function |

## WHAT

### New function in `directory_utils.py`

```python
def is_path_in_git_dir(path: str) -> bool:
    """Check if a path is inside a .git directory."""
```

### Refactored function

`_discover_files()` — replace inline `.git` check with `is_path_in_git_dir()`.

## HOW

- Add `is_path_in_git_dir()` above `_discover_files()` in `directory_utils.py`
- In `_discover_files()`, replace the `if ".git" in dirs: dirs.remove(".git")` block with a call filtering dirs via the new helper
- No import changes needed — same module

## ALGORITHM

```python
def is_path_in_git_dir(path: str) -> bool:
    return ".git" in Path(path).parts
```

For `_discover_files()` refactor:
```python
# Before:
if ".git" in dirs:
    dirs.remove(".git")

# After:
dirs[:] = [d for d in dirs if not is_path_in_git_dir(d)]
```

## DATA

- **Input:** `path: str` — relative or absolute path
- **Output:** `bool` — `True` if any path component is literally `.git`

## Tests (TDD — write first)

```python
# tests/file_tools/test_directory_utils.py

def test_is_path_in_git_dir_with_git_config():
    """Path .git/config is inside .git directory."""
    assert is_path_in_git_dir(".git/config") is True

def test_is_path_in_git_dir_with_git_hooks():
    """Path .git/hooks/pre-commit is inside .git directory."""
    assert is_path_in_git_dir(".git/hooks/pre-commit") is True

def test_is_path_in_git_dir_normal_file():
    """Normal file path is not inside .git."""
    assert is_path_in_git_dir("src/main.py") is False

def test_is_path_in_git_dir_gitignore_file():
    """.gitignore is NOT inside .git directory (it's a regular file)."""
    assert is_path_in_git_dir(".gitignore") is False

def test_is_path_in_git_dir_dot_git_only():
    """Bare .git path is inside .git directory."""
    assert is_path_in_git_dir(".git") is True

def test_git_directory_exclusion_still_works():
    """Existing test — verify _discover_files() still excludes .git after refactor."""
    # (existing test_git_directory_exclusion already covers this)
```

## Commit Message

```
Add is_path_in_git_dir helper and DRY-refactor _discover_files
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

Implement step 1: Add `is_path_in_git_dir()` to `directory_utils.py` and refactor `_discover_files()` to use it.

Follow TDD:
1. Write the tests in tests/file_tools/test_directory_utils.py first
2. Implement `is_path_in_git_dir()` in directory_utils.py
3. Refactor `_discover_files()` to use the new helper
4. Run all three code quality checks (pylint, pytest, mypy) — all must pass
5. Verify existing test_git_directory_exclusion still passes (regression check)
```
