# Step 1: Rename `_safe_repo_context` → `safe_repo_context`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: rename `_safe_repo_context` to `safe_repo_context` in `core.py` and update all internal references across the git_operations submodules. This is a mechanical rename — no logic changes. Run all quality checks after.

## WHERE

**Definition:**
- `src/mcp_workspace/git_operations/core.py` — rename the function definition

**Import + usage sites (11 files):**
- `src/mcp_workspace/git_operations/branch_queries.py`
- `src/mcp_workspace/git_operations/branches.py`
- `src/mcp_workspace/git_operations/commits.py`
- `src/mcp_workspace/git_operations/diffs.py`
- `src/mcp_workspace/git_operations/file_tracking.py`
- `src/mcp_workspace/git_operations/parent_branch_detection.py`
- `src/mcp_workspace/git_operations/remotes.py`
- `src/mcp_workspace/git_operations/repository_status.py`
- `src/mcp_workspace/git_operations/staging.py`
- `src/mcp_workspace/git_operations/read_operations.py`
- `src/mcp_workspace/git_operations/workflows.py`

## WHAT

No new functions. Rename only:
- `_safe_repo_context(project_dir: Path) -> Iterator[Repo]` becomes `safe_repo_context(project_dir: Path) -> Iterator[Repo]`

## HOW

Mechanical find-and-replace in each file:
1. In import lines: `_safe_repo_context` → `safe_repo_context`
2. In `with` statements: `with _safe_repo_context(` → `with safe_repo_context(`

## ALGORITHM

```
for each file in [core.py] + 11 submodules:
    replace "_safe_repo_context" with "safe_repo_context" (all occurrences)
for each test file that mocks _safe_repo_context by dotted path string:
    replace the old dotted path with the renamed one
run pylint, mypy, pytest → all must pass
```

**Test files with mock patch strings that must be updated:**
- `tests/git_operations/test_read_operations.py` — 10 occurrences of `"mcp_workspace.git_operations.read_operations._safe_repo_context"`
- `tests/git_operations/test_parent_branch_detection.py` — 1 occurrence of `"mcp_workspace.git_operations.parent_branch_detection._safe_repo_context"`

## DATA

No data structure changes. Function signature and return type are unchanged.

## TESTS

Existing tests already exercise `_safe_repo_context` indirectly through all the submodule functions. No new tests needed — the rename is verified by the existing test suite passing.

**Important:** Some test files mock `_safe_repo_context` by full dotted path string (e.g., `"mcp_workspace.git_operations.read_operations._safe_repo_context"`). These mock target strings must also be renamed to use `safe_repo_context`, otherwise the mocks won't patch the correct target and tests will fail.

## COMMIT

`refactor: rename _safe_repo_context to safe_repo_context for public API`
