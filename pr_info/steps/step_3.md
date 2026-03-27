# Step 3: Enforce Gitignore in All Server File Tools

> **Context:** See `pr_info/steps/summary.md` for the full plan. This is step 3 of 3.
> **Depends on:** Step 2 (`is_path_gitignored()` must exist).

## Goal

Add a `_check_not_gitignored()` guard function in `server.py` and call it at the top of every affected tool handler. This is the policy enforcement layer.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_workspace/server.py` | Add guard function, call in 6 tool handlers |
| `tests/test_server.py` | Add tests for gitignore enforcement in all tools |

## WHAT

### New function in `server.py`

```python
def _check_not_gitignored(file_path: str) -> None:
    """Raise ValueError if path is excluded by .gitignore.

    This is a security boundary — always enforced, no toggle.
    """
```

### Modified tool handlers

Add `_check_not_gitignored(file_path)` call at the top of:
- `read_file(file_path)` — after input validation, before `read_file_util()`
- `save_file(file_path, content)` — after input validation, before `save_file_util()`
- `append_file(file_path, content)` — after input validation, before `append_file_util()`
- `edit_file(file_path, edits, ...)` — after input validation, before `edit_file_util()`
- `delete_this_file(file_path)` — after input validation, before `delete_file_util()`
- `move_file(source_path, destination_path)` — check **both** paths, after input validation

### NOT modified

- `list_directory()` — already filters via `use_gitignore=True`
- `read_reference_file()` — operates on separate reference project directories
- `list_reference_directory()` — operates on separate reference project directories

## HOW

- Import `is_path_gitignored` from `mcp_workspace.file_tools.directory_utils` in `server.py`
- Add `_check_not_gitignored()` as a module-level helper (private, not a tool)
- Insert one-line calls in each handler, after existing input validation but before business logic

### Import addition in `server.py`

```python
from mcp_workspace.file_tools.directory_utils import is_path_gitignored
```

## ALGORITHM

```python
def _check_not_gitignored(file_path: str) -> None:
    if _project_dir is None:
        return  # Can't check without project_dir; other validation will catch this
    # Normalize to relative path for gitignore checking
    path = Path(file_path)
    if path.is_absolute():
        try:
            file_path = str(path.relative_to(_project_dir))
        except ValueError:
            return  # Path outside project dir — other validation handles this
    if is_path_gitignored(file_path, _project_dir):
        raise ValueError(
            f"File '{file_path}' is excluded by .gitignore and cannot be accessed. "
            "Use list_directory() to see available files."
        )
```

### Integration pattern (same for each tool)

```python
@mcp.tool()
def read_file(file_path: str) -> str:
    # ... existing input validation ...
    _check_not_gitignored(file_path)      # ← ADD THIS LINE
    # ... existing business logic ...
```

### For `move_file` specifically

> **Important:** Place gitignore checks **before** the existing `try/except` block in `move_file`, because that block catches `ValueError` and rewrites the message to `'Invalid operation'`, which would hide the gitignore error.

```python
@mcp.tool()
def move_file(source_path: str, destination_path: str) -> bool:
    # ... existing input validation ...
    _check_not_gitignored(source_path)       # ← BEFORE try/except block
    _check_not_gitignored(destination_path)   # ← BEFORE try/except block
    try:
        # ... existing business logic ...
```

## DATA

- **Input:** `file_path: str` (relative path)
- **Output:** `None` (raises `ValueError` if blocked)
- **Error message format:** `"File '<path>' is excluded by .gitignore and cannot be accessed. Use list_directory() to see available files."`

## Tests (TDD — write first)

Tests use a real tmp_path with a `.gitignore` file. The `setup_server` fixture sets `_project_dir`, so we just need to ensure `.gitignore` exists in that directory.

```python
# tests/test_server.py

@pytest.fixture
def gitignore_project(project_dir):
    """Project dir with a .gitignore that blocks *.log and __pycache__/."""
    (project_dir / ".gitignore").write_text("*.log\n__pycache__/\n")
    return project_dir


# --- Blocked operations ---

def test_read_file_gitignored(gitignore_project):
    """read_file on gitignored file raises ValueError."""
    (gitignore_project / "debug.log").write_text("log content")
    with pytest.raises(ValueError, match="excluded by .gitignore"):
        read_file("debug.log")

def test_save_file_gitignored(gitignore_project):
    """save_file to gitignored path raises ValueError."""
    with pytest.raises(ValueError, match="excluded by .gitignore"):
        save_file("output.log", "content")

def test_edit_file_gitignored(gitignore_project):
    """edit_file on gitignored file raises ValueError."""
    with pytest.raises(ValueError, match="excluded by .gitignore"):
        edit_file("debug.log", [{"old_text": "a", "new_text": "b"}])

def test_append_file_gitignored(gitignore_project):
    """append_file to gitignored file raises ValueError."""
    (gitignore_project / "debug.log").write_text("existing")
    with pytest.raises(ValueError, match="excluded by .gitignore"):
        append_file("debug.log", "more")

def test_delete_file_gitignored(gitignore_project):
    """delete_this_file on gitignored file raises ValueError."""
    (gitignore_project / "debug.log").write_text("to delete")
    with pytest.raises(ValueError, match="excluded by .gitignore"):
        delete_this_file("debug.log")

def test_move_file_gitignored_source(gitignore_project):
    """move_file with gitignored source raises ValueError."""
    (gitignore_project / "debug.log").write_text("content")
    with pytest.raises(ValueError, match="excluded by .gitignore"):
        move_file("debug.log", "renamed.txt")

def test_move_file_gitignored_destination(gitignore_project):
    """move_file with gitignored destination raises ValueError."""
    (gitignore_project / "safe.txt").write_text("content")
    with pytest.raises(ValueError, match="excluded by .gitignore"):
        move_file("safe.txt", "output.log")


# --- Directory patterns ---

def test_read_file_in_gitignored_directory(gitignore_project):
    """File inside gitignored directory (__pycache__/) is blocked."""
    cache_dir = gitignore_project / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "module.pyc").write_text("bytecode")
    with pytest.raises(ValueError, match="excluded by .gitignore"):
        read_file("__pycache__/module.pyc")


# --- .git/ directory ---

def test_read_file_git_config(gitignore_project):
    """read_file on .git/config is blocked."""
    git_dir = gitignore_project / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("[core]")
    with pytest.raises(ValueError, match="excluded by .gitignore"):
        read_file(".git/config")

def test_save_file_git_hooks(gitignore_project):
    """save_file to .git/hooks/ is blocked."""
    with pytest.raises(ValueError, match="excluded by .gitignore"):
        save_file(".git/hooks/pre-commit", "#!/bin/sh")


# --- Normal operation ---

def test_read_file_not_gitignored(gitignore_project):
    """Non-gitignored file works normally."""
    (gitignore_project / "readme.txt").write_text("hello")
    content = read_file("readme.txt")
    assert content == "hello"

def test_save_file_not_gitignored(gitignore_project):
    """Non-gitignored save works normally."""
    result = save_file("readme.txt", "hello")
    assert result is True


# --- No .gitignore ---

def test_read_file_no_gitignore(project_dir):
    """Without .gitignore, all files are accessible."""
    (project_dir / "debug.log").write_text("log content")
    content = read_file("debug.log")
    assert content == "log content"
```

## Commit Message

```
Enforce gitignore as security boundary in all file tools
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for full context.

Implement step 3: Add `_check_not_gitignored()` guard in `server.py` and enforce it in all 6 affected tool handlers.

Follow TDD:
1. Write the tests in tests/test_server.py first (import delete_this_file, edit_file, move_file at the top alongside existing imports)
2. Add the import of `is_path_gitignored` from `directory_utils` in server.py
3. Add `_check_not_gitignored()` helper function in server.py
4. Add the guard call in each of the 6 tool handlers — after input validation, before business logic
5. For move_file, check BOTH source_path and destination_path
6. Run all three code quality checks (pylint, pytest, mypy) — all must pass
7. Run the full test suite including existing tests to verify no regressions
```
