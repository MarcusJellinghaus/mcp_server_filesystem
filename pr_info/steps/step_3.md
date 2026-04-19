# Step 3: Read Operations Module

> **Context**: See `pr_info/steps/summary.md` for full architecture overview.

## LLM Prompt

```
Implement step 3 of issue #77 (read-only git operations).
Read pr_info/steps/summary.md for context, then read this step file.
Create the read operations module with git_log, git_diff, git_status, git_merge_base,
plus integration tests using real git repos. Follow TDD.
Run all code quality checks after implementation. Produce one commit.
```

## WHERE

- **New**: `src/mcp_workspace/git_operations/read_operations.py`
- **New**: `tests/git_operations/test_read_operations.py`

## WHAT

### `read_operations.py`

```python
import logging
import os
from pathlib import Path
from typing import Optional

from .arg_validation import validate_args
from .compact_diffs import render_compact_diff
from .core import _safe_repo_context
from .output_filtering import filter_diff_output, filter_log_output, truncate_output

logger = logging.getLogger(__name__)

# Hardcoded safety flags — defense-in-depth against external program execution
_SAFETY_FLAGS: list[str] = ["--no-ext-diff", "--no-textconv"]

def git_log(
    project_dir: Path,
    args: Optional[list[str]] = None,
    pathspec: Optional[list[str]] = None,
    search: Optional[str] = None,
    max_lines: int = 50,
) -> str: ...

def git_diff(
    project_dir: Path,
    args: Optional[list[str]] = None,
    pathspec: Optional[list[str]] = None,
    search: Optional[str] = None,
    context: int = 3,
    max_lines: int = 100,
    compact: bool = True,
) -> str: ...

def git_status(
    project_dir: Path,
    args: Optional[list[str]] = None,
    max_lines: int = 200,
) -> str: ...

def git_merge_base(
    project_dir: Path,
    args: Optional[list[str]] = None,
) -> str: ...
```

## HOW

- All functions use `_safe_repo_context()` from `core.py` for Windows handle safety
- All functions call `validate_args()` before executing any git command
- `git_diff` and `git_log` prepend `_SAFETY_FLAGS` to every invocation
- `pathspec` is appended after `"--"` (injected by the tool, never from user args)
- Git commands executed via `repo.git.log()`, `repo.git.diff()`, etc. (GitPython)

## ALGORITHM — `git_log`

```
1. validate_args("log", args)
2. Build cmd_args = _SAFETY_FLAGS + (args or [])
3. If pathspec: cmd_args += ["--"] + pathspec
4. with _safe_repo_context(project_dir) as repo:
     output = repo.git.log(*cmd_args)
5. If not output: return "No commits found"
6. If search: output = filter_log_output(output, search)
7. return truncate_output(output, max_lines)
```

## ALGORITHM — `git_diff`

```
1. validate_args("diff", args)
2. user_args = args or []
3. with _safe_repo_context(project_dir) as repo:
   If compact:
     a. Strip any color-related args from user_args
        (strip any arg starting with `--color`; note: `--color-words` from the allowlist is incompatible with compact mode and should be stripped when compact=True)
     b. Inject -M -C90% for move/copy detection
     c. Build base_args = _SAFETY_FLAGS + final_args + (["--"] + pathspec if pathspec else [])
     d. plain = repo.git.diff(*base_args)
     e. ansi = repo.git.diff("--color=always", "--color-moved=dimmed-zebra", *base_args)
     f. output = render_compact_diff(plain, ansi)
     g. If line count reduced: prepend stats header
   Else:
     a. Build cmd_args = _SAFETY_FLAGS + user_args + (["--"] + pathspec if pathspec else [])
     b. output = repo.git.diff(*cmd_args)
4. If not output: return "No changes found"
5. If search: output = filter_diff_output(output, search, context)
6. return truncate_output(output, max_lines)
```

## ALGORITHM — `git_status`

```
1. validate_args("status", args)
2. Build cmd_args = args or []
3. with _safe_repo_context(project_dir) as repo:
     output = repo.git.status(*cmd_args)
4. If not output: return "No changes found"
5. return truncate_output(output, max_lines)
```

## ALGORITHM — `git_merge_base`

```
1. validate_args("merge_base", args)
2. Build cmd_args = args or []
3. with _safe_repo_context(project_dir) as repo:
     output = repo.git.merge_base(*cmd_args)
     For --is-ancestor: catch GitCommandError; exit code 1 → return "false", exit code 0 → return "true"
4. If not output: return "No common ancestor found"
5. return output
```

**Note:** `git merge-base --is-ancestor` communicates via exit codes, not stdout. Exit code 0 means "is ancestor" (return `"true"`), exit code 1 means "not ancestor" (return `"false"`). GitPython raises `GitCommandError` for non-zero exit codes, so the implementation must catch this.

## DATA

### Return Values

All functions return `str`:
- Raw git output (possibly filtered/truncated)
- Or a descriptive empty-result message

### Stats Header Format (compact diff)

```
# Compact diff: {before} → {after} lines ({pct}% reduction, {suppressed} moved lines suppressed)
```

Only prepended when `render_compact_diff` actually reduces line count.

## TEST CASES (`test_read_operations.py`)

All tests use the `git_repo_with_commit` fixture from `conftest.py` and are marked `@pytest.mark.git_integration`.

```python
@pytest.mark.git_integration
class TestGitLog:
    def test_basic_log_returns_commits(): ...
    def test_log_with_oneline(): ...
    def test_log_with_pathspec(): ...
    def test_log_search_filters_output(): ...
    def test_log_max_lines_truncates(): ...
    def test_log_empty_repo_message(): ...
    def test_log_rejected_flag_raises(): ...
    def test_log_hardcodes_safety_flags(): ...  # mock repo.git.log to verify --no-ext-diff --no-textconv in args

@pytest.mark.git_integration
class TestGitDiff:
    def test_basic_diff_returns_changes(): ...
    def test_diff_staged(): ...
    def test_diff_between_refs(): ...
    def test_diff_with_pathspec(): ...
    def test_diff_compact_default(): ...       # compact=True is default
    def test_diff_compact_false_raw(): ...
    def test_diff_search_filters(): ...
    def test_diff_max_lines_truncates(): ...
    def test_diff_no_changes_message(): ...
    def test_diff_rejected_flag_raises(): ...
    def test_diff_hardcodes_safety_flags(): ...  # mock repo.git.diff to verify --no-ext-diff --no-textconv in args

@pytest.mark.git_integration
class TestGitStatus:
    def test_status_clean_repo(): ...
    def test_status_with_changes(): ...
    def test_status_short_flag(): ...
    def test_status_max_lines_truncates(): ...
    def test_status_rejected_flag_raises(): ...

@pytest.mark.git_integration
class TestGitMergeBase:
    # Note: these tests create additional branches within the test body
    # using the repo from git_repo_with_commit; the shared fixture is not modified.
    def test_merge_base_two_branches(): ...     # create a second branch to have common ancestor
    def test_merge_base_is_ancestor(): ...      # --is-ancestor with valid ancestor returns "true"
    def test_merge_base_not_ancestor(): ...     # --is-ancestor with non-ancestor returns "false"
    def test_merge_base_rejected_flag_raises(): ...
```
