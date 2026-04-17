# Step 2: Move 13 source files — replace flat module with package

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. This is step 2 of 3 for issue #98.
>
> Replace the flat module `src/mcp_workspace/file_tools/git_operations.py` with a package
> containing 13 files copied from `mcp_coder.utils.git_operations`. Fix all internal imports.
> The existing consumers (`file_operations.py`, `file_tools/__init__.py`) must continue working
> without changes — the package `__init__.py` re-exports the same 3 names.
>
> Use `get_library_source` to read each of mcp_coder's 13 source files, then copy them
> with import paths rewritten. Run all checks after.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_workspace/file_tools/git_operations.py` | Delete |
| `src/mcp_workspace/file_tools/git_operations/__init__.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/core.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/branches.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/branch_queries.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/commits.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/compact_diffs.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/diffs.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/file_tracking.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/parent_branch_detection.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/remotes.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/repository_status.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/staging.py` | Create |
| `src/mcp_workspace/file_tools/git_operations/workflows.py` | Create |

No changes to `file_operations.py` or `file_tools/__init__.py` — imports resolve automatically.

## WHAT

### Reading source files

Use `get_library_source` to read each file from the installed `mcp_coder` package:

```
mcp_coder.utils.git_operations          → __init__.py
mcp_coder.utils.git_operations.core     → core.py
mcp_coder.utils.git_operations.branches → branches.py
... (all 13 files)
```

### Import rewrites (applied to every file)

| Find | Replace |
|------|---------|
| `from mcp_coder.utils.git_operations` | `from mcp_workspace.file_tools.git_operations` |
| `import mcp_coder.utils.git_operations` | `import mcp_workspace.file_tools.git_operations` |
| `mcp_coder.utils.git_operations` (in strings/comments) | `mcp_workspace.file_tools.git_operations` |

### Additional import fix in `commits.py`

| Find | Replace |
|------|---------|
| `from mcp_coder.utils.subprocess_runner` | `from mcp_coder_utils.subprocess_runner` |

This is Decision 13 from the issue — required to avoid forbidden `mcp_coder` runtime dependency.

### `__init__.py` — trimmed re-export

The new `__init__.py` must re-export exactly 3 names (Decision 10):

```python
from mcp_workspace.file_tools.git_operations.repository_status import is_git_repository
from mcp_workspace.file_tools.git_operations.file_tracking import is_file_tracked, git_move

__all__ = ["is_git_repository", "is_file_tracked", "git_move"]
```

**Important**: Verify which submodule each function lives in by reading the source. The mapping above is based on the issue description — `git_move` may be in `staging.py` or `core.py`. Adjust as needed.

Do NOT copy mcp_coder's full `__all__` with ~30 symbols. Only the 3 above.

## HOW

Integration points that must keep working after the move:

1. `file_tools/__init__.py` line: `from mcp_workspace.file_tools.git_operations import (git_move, is_file_tracked, is_git_repository)` — resolved via package `__init__.py`
2. `file_operations.py` lines: `from mcp_workspace.file_tools.git_operations import git_move as git_move_impl` and `import is_file_tracked, is_git_repository` — same resolution
3. `test_move_git_integration.py` patch: `mcp_workspace.file_tools.file_operations.git_move_impl` — unchanged (patches the import in file_operations, not git_operations)

**Note:** The issue's acceptance criterion "file_tools/file_operations.py and file_tools/__init__.py imports updated" is satisfied by the package `__init__.py` re-export — no edits needed to those files.

## ALGORITHM

```
1. Read all 13 files from mcp_coder.utils.git_operations via get_library_source
2. For each file: rewrite mcp_coder.utils.git_operations → mcp_workspace.file_tools.git_operations
3. For commits.py: additionally rewrite mcp_coder.utils.subprocess_runner → mcp_coder_utils.subprocess_runner
4. Write trimmed __init__.py (only 3 re-exports, not mcp_coder's full __all__)
5. Delete src/mcp_workspace/file_tools/git_operations.py (flat module)
6. Run pylint, mypy, pytest — all must pass
```

## DATA

No new data structures. Same function signatures, same return types.

### Verification

After this step:
- `from mcp_workspace.file_tools.git_operations import is_git_repository` works
- `from mcp_workspace.file_tools.git_operations.core import _safe_repo_context` works
- `from mcp_workspace.file_tools import git_move` works (via chain: `file_tools/__init__.py` → `git_operations/__init__.py` → `file_tracking.py`)
- Existing tests in `test_move_git_integration.py` pass unchanged
- No `mcp_coder` imports in `src/` (grep with pattern excluding `mcp_coder_utils`)

## Commit message

```
feat: replace git_operations flat module with mcp_coder's package (13 files)

Replace src/mcp_workspace/file_tools/git_operations.py with full
git_operations/ package from mcp_coder. Adds Windows handle safety
via _safe_repo_context and superset git functions.

Import rewrites:
- mcp_coder.utils.git_operations → mcp_workspace.file_tools.git_operations
- commits.py: mcp_coder.utils.subprocess_runner → mcp_coder_utils.subprocess_runner

Trimmed re-export: only is_git_repository, is_file_tracked, git_move.
Existing consumers (file_operations.py, file_tools/__init__.py) unchanged.

Part of #98 — move git_operations into mcp_workspace (step 2/3)
```
