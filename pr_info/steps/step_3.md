# Step 3: Move tests, consolidate edge cases, delete old test file

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. This is step 3 of 3 for issue #98.
>
> Move 14 test files from mcp_coder into `tests/file_tools/git_operations/`.
> Consolidate 5 unique edge-case tests from the existing `test_git_operations.py` into
> `test_edge_cases.py`, update mock-patch paths, then delete the old flat test file.
> Run all checks after.
>
> Use `get_library_source` to read mcp_coder's test files. The test conftest.py and
> 12 test_*.py files are under `mcp_coder.tests.utils.git_operations` (or read from
> the installed package's test directory).

## WHERE

| File | Action |
|------|--------|
| `tests/file_tools/git_operations/__init__.py` | Create |
| `tests/file_tools/git_operations/conftest.py` | Create |
| `tests/file_tools/git_operations/test_core.py` | Create |
| `tests/file_tools/git_operations/test_branches.py` | Create |
| `tests/file_tools/git_operations/test_branch_queries.py` | Create |
| `tests/file_tools/git_operations/test_commits.py` | Create |
| `tests/file_tools/git_operations/test_compact_diffs.py` | Create |
| `tests/file_tools/git_operations/test_compact_diffs_header_only.py` | Create |
| `tests/file_tools/git_operations/test_diffs.py` | Create |
| `tests/file_tools/git_operations/test_file_tracking.py` | Create |
| `tests/file_tools/git_operations/test_remotes.py` | Create |
| `tests/file_tools/git_operations/test_repository_status.py` | Create |
| `tests/file_tools/git_operations/test_staging.py` | Create |
| `tests/file_tools/git_operations/test_edge_cases.py` | Create (consolidated) |
| `tests/file_tools/test_git_operations.py` | Delete |

## WHAT

### Part A: Move 14 test files from mcp_coder

Copy `conftest.py` + 12 `test_*.py` files + `__init__.py` from mcp_coder's `tests/utils/git_operations/` into `tests/file_tools/git_operations/`.

**Import rewrites in every test file:**

| Find | Replace |
|------|---------|
| `from mcp_coder.utils.git_operations` | `from mcp_workspace.file_tools.git_operations` |
| `import mcp_coder.utils.git_operations` | `import mcp_workspace.file_tools.git_operations` |

**Test markers:**
- Most tests are `@pytest.mark.git_integration` — this works because step 1 registered the marker.
- `test_compact_diffs.py` and `test_compact_diffs_header_only.py` are intentionally **unmarked** (pure string tests, no git).

**Conftest fixtures** (`git_repo`, `git_repo_with_commit`, `git_repo_with_remote`) are scoped to `tests/file_tools/git_operations/`. No collision with `tests/conftest.py`.

### Part B: Consolidate edge cases from existing test file

From `tests/file_tools/test_git_operations.py`, identify:

**3 DUPLICATE tests to discard** (covered by incoming tests):
- `test_is_git_repository_with_actual_repo`
- `test_is_file_tracked_without_git`
- `test_is_file_tracked_with_git`

**5 UNIQUE tests to consolidate** into `tests/file_tools/git_operations/test_edge_cases.py`:
- `test_is_git_repository_with_invalid_repo` — bare `.git` dir detection
- `test_is_file_tracked_outside_repo` — file outside repo boundary
- `test_is_file_tracked_with_staged_file` — staged but uncommitted
- `test_is_git_repository_with_exception` — mock-based, exception branch
- `test_is_file_tracked_with_git_error` — mock-based, GitCommandError branch

### Part C: Update mock-patch paths in consolidated tests

The 2 mock-based tests currently patch `mcp_workspace.file_tools.git_operations.Repo`. Because `Repo` is now imported inside `core.py`, update to:

```python
# OLD
@patch("mcp_workspace.file_tools.git_operations.Repo")

# NEW
@patch("mcp_workspace.file_tools.git_operations.core.Repo")
```

### Part D: Delete old test file

Delete `tests/file_tools/test_git_operations.py` after consolidation.

## HOW

### `test_edge_cases.py` structure

```python
"""Edge-case tests for git operations (consolidated from test_git_operations.py)."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from git import Repo
from git.exc import GitCommandError

from mcp_workspace.file_tools.git_operations import is_file_tracked, is_git_repository


class TestGitEdgeCases:
    """Edge-case tests for git repository and file tracking detection."""

    def test_is_git_repository_with_invalid_repo(self, tmp_path: Path) -> None:
        """Test detection when .git exists but is invalid."""
        ...

    def test_is_file_tracked_outside_repo(self, tmp_path: Path) -> None:
        """Test file tracking for file outside repository."""
        ...

    def test_is_file_tracked_with_staged_file(self, tmp_path: Path) -> None:
        """Test detection of staged but uncommitted files."""
        ...

    @patch("mcp_workspace.file_tools.git_operations.core.Repo")
    def test_is_git_repository_with_exception(self, mock_repo: Mock, tmp_path: Path) -> None:
        """Test handling of unexpected exceptions."""
        ...

    @patch("mcp_workspace.file_tools.git_operations.core.Repo")
    def test_is_file_tracked_with_git_error(self, mock_repo: Mock, tmp_path: Path) -> None:
        """Test handling of git command errors."""
        ...
```

**Note on `test_is_file_tracked_with_git_error` mock target**: This test patches `Repo` and then calls `is_file_tracked`. Verify that `is_file_tracked` (in `file_tracking.py`) uses `Repo` imported from `core.py` via `_safe_repo_context` or directly. If `file_tracking.py` imports `Repo` directly, the patch target should be `mcp_workspace.file_tools.git_operations.file_tracking.Repo`. Read the source to determine the correct target.

## ALGORITHM

```
1. Read 14 test files from mcp_coder (get_library_source or reference project)
2. Rewrite imports: mcp_coder.utils.git_operations → mcp_workspace.file_tools.git_operations
3. Write all files to tests/file_tools/git_operations/
4. Create test_edge_cases.py with 5 unique tests from test_git_operations.py
5. Update 2 mock-patch paths to ...core.Repo (or correct submodule — verify)
6. Delete tests/file_tools/test_git_operations.py
7. Run pylint, mypy, pytest — all must pass
```

## DATA

No new data structures. Test functions only.

### Verification

- `pytest tests/file_tools/git_operations/ -n auto` — all tests pass
- `pytest tests/file_tools/test_move_git_integration.py` — still passes (unchanged)
- `pytest -m git_integration -n auto` — runs without marker warnings
- `pytest -m "not git_integration" -n auto` — runs compact_diffs tests (unmarked)
- No file `tests/file_tools/test_git_operations.py` exists
- No file `tests/integration_test_move.py` exists (deleted in step 1)

## Commit message

```
test: move 14 test files, consolidate edge cases, clean up old test file

- Move 12 test_*.py + conftest.py + __init__.py from mcp_coder
- Consolidate 5 unique edge cases into test_edge_cases.py
- Update mock-patch paths to git_operations.core.Repo
- Delete tests/file_tools/test_git_operations.py (3 duplicates removed)

Part of #98 — move git_operations into mcp_workspace (step 3/3)
```
