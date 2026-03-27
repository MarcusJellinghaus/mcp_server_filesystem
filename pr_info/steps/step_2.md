# Step 2: Add `is_path_gitignored()` Utility Function

> **Context:** See `pr_info/steps/summary.md` for the full plan. This is step 2 of 3.
> **Depends on:** Step 1 (`is_path_in_git_dir()` must exist).

## Goal

Add `is_path_gitignored()` to `directory_utils.py` — the core check logic that determines whether a given path is blocked by `.gitignore` or `.git/`. This function is MCP-agnostic and will be called by the server guard in step 3.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_workspace/file_tools/directory_utils.py` | Add `is_path_gitignored()` |
| `tests/file_tools/test_directory_utils.py` | Add tests |

## WHAT

### New function in `directory_utils.py`

```python
def is_path_gitignored(file_path: str, project_dir: Path) -> bool:
    """Check if a path is blocked by .gitignore rules or is inside .git/.

    Works on both existing and non-existing paths (e.g., blocks saving
    a new file to a gitignored pattern like *.log).

    Args:
        file_path: Relative path to check (relative to project_dir)
        project_dir: Project root directory containing .gitignore

    Returns:
        True if the path should be blocked
    """
```

## HOW

- Add function after `is_path_in_git_dir()` in `directory_utils.py`
- Reuse existing `read_gitignore_rules()` — no new parsing infrastructure
- No changes to `__init__.py` needed yet (server.py will import directly in step 3)

## ALGORITHM

```python
def is_path_gitignored(file_path: str, project_dir: Path) -> bool:
    if is_path_in_git_dir(file_path):
        return True
    gitignore_path = project_dir / ".gitignore"
    matcher, _ = read_gitignore_rules(gitignore_path)
    if matcher is None:
        return False
    abs_path = str(project_dir / file_path)
    return matcher(abs_path)
```

## DATA

- **Input:** `file_path: str` (relative path), `project_dir: Path`
- **Output:** `bool` — `True` if path is blocked

## Tests (TDD — write first)

All tests create a temp directory with a `.gitignore` file and exercise `is_path_gitignored()` directly.

```python
# tests/file_tools/test_directory_utils.py

def test_is_path_gitignored_log_file(tmp_path):
    """*.log pattern blocks .log files."""
    (tmp_path / ".gitignore").write_text("*.log\n")
    assert is_path_gitignored("debug.log", tmp_path) is True

def test_is_path_gitignored_normal_file(tmp_path):
    """Normal .py file is not blocked."""
    (tmp_path / ".gitignore").write_text("*.log\n")
    assert is_path_gitignored("main.py", tmp_path) is False

def test_is_path_gitignored_pycache_dir(tmp_path):
    """__pycache__/ pattern blocks files inside __pycache__."""
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    assert is_path_gitignored("__pycache__/module.pyc", tmp_path) is True

def test_is_path_gitignored_git_dir(tmp_path):
    """.git/ paths are always blocked even without .gitignore."""
    assert is_path_gitignored(".git/config", tmp_path) is True

def test_is_path_gitignored_no_gitignore(tmp_path):
    """No .gitignore file means nothing is blocked."""
    assert is_path_gitignored("anything.log", tmp_path) is False

def test_is_path_gitignored_nonexistent_file(tmp_path):
    """Non-existent file matching pattern is still blocked (security for save_file)."""
    (tmp_path / ".gitignore").write_text("*.log\n")
    # File does NOT exist, but pattern matches — must still block
    assert is_path_gitignored("new_debug.log", tmp_path) is True

def test_is_path_gitignored_nested_in_ignored_dir(tmp_path):
    """File deep inside an ignored directory is blocked."""
    (tmp_path / ".gitignore").write_text(".venv/\n")
    assert is_path_gitignored(".venv/lib/python3.11/site.py", tmp_path) is True

def test_is_path_gitignored_gitignore_file_itself(tmp_path):
    """.gitignore file itself is not blocked."""
    (tmp_path / ".gitignore").write_text("*.log\n")
    assert is_path_gitignored(".gitignore", tmp_path) is False
```

## Commit Message

```
Add is_path_gitignored utility function
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.

Implement step 2: Add `is_path_gitignored()` to `directory_utils.py`.

Follow TDD:
1. Write the tests in tests/file_tools/test_directory_utils.py first
2. Implement `is_path_gitignored()` in directory_utils.py
3. Run all three code quality checks (pylint, pytest, mypy) — all must pass
4. Pay special attention to the __pycache__/ and .venv/ directory pattern tests — verify IgnoreParser handles these correctly. If it doesn't, add parent-component checking logic.
```
