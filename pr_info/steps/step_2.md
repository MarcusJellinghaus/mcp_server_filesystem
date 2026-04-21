# Step 2: Expand `__init__.py` with 19 new re-exports

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2: add the 19 missing symbol re-exports to `git_operations/__init__.py`, update `__all__`, and add externally-consumed symbols to `vulture_whitelist.py`. Run all quality checks after.

## WHERE

- `src/mcp_workspace/git_operations/__init__.py` — add imports + `__all__` entries
- `vulture_whitelist.py` — add newly-exported symbols unused within mcp_workspace

## WHAT

Add 19 new re-exports to the package's public API. No new functions or classes — all symbols already exist in submodules.

### Symbols to add (grouped by submodule)

**From `branch_queries`:**
- `extract_issue_number_from_branch`
- `has_remote_tracking_branch`
- `validate_branch_name`

**From `commits`:**
- `commit_staged_files`
- `get_latest_commit_sha`

**From `compact_diffs`:**
- `get_compact_diff`

**From `core`:**
- `CommitResult`
- `safe_repo_context` (renamed in Step 1)

**From `diffs`:**
- `get_branch_diff`
- `get_git_diff_for_commit`

**From `parent_branch_detection`:**
- `MERGE_BASE_DISTANCE_THRESHOLD`
- `detect_parent_branch_via_merge_base`

**From `remotes`:**
- `git_push`
- `rebase_onto_branch`

**From `repository_status`:**
- `get_full_status`
- `is_working_directory_clean`

**From `staging`:**
- `stage_all_changes`

**From `workflows`:**
- `commit_all_changes`
- `needs_rebase`

## HOW

1. Add import statements to `__init__.py` grouped by submodule (matching existing style)
2. Add all 19 symbols to `__all__` list in alphabetical order (matching existing style)
3. Add symbols to vulture whitelist that are only consumed externally

## ALGORITHM

```
add import blocks for each submodule with new symbols
extend __all__ list with 19 new entries (alphabetical)
add externally-consumed symbols to vulture_whitelist.py
run pylint, mypy, pytest → all must pass
```

## DATA

No new data structures. `CommitResult` is a `TypedDict` already defined in `core.py`:
```python
class CommitResult(TypedDict):
    success: bool
    commit_hash: Optional[str]
    error: Optional[str]
```

## TESTS

**New test file:** `tests/git_operations/test_init_exports.py`

Verify all 33 symbols (14 existing + 19 new) are importable from `mcp_workspace.git_operations`:

```python
def test_all_expected_symbols_exported():
    """Verify all symbols from __all__ are importable."""
    from mcp_workspace import git_operations
    for name in git_operations.__all__:
        assert hasattr(git_operations, name), f"Missing export: {name}"

def test_expected_symbol_count():
    """Verify __all__ has the expected 33 symbols."""
    from mcp_workspace.git_operations import __all__
    assert len(__all__) == 33
```

## VULTURE WHITELIST

Symbols that are exported but not used within mcp_workspace itself need to be added to `vulture_whitelist.py`. Check each of the 19 new exports against internal usage:

Likely candidates for whitelist (consumed only by mcp_coder externally):
- `safe_repo_context`
- `CommitResult` (used in workflows.py type annotation — may not need whitelist)
- `commit_staged_files` (used in workflows.py — may not need whitelist)
- `get_compact_diff`
- `get_git_diff_for_commit`
- `git_push`
- `rebase_onto_branch`
- `commit_all_changes`
- `needs_rebase`
- `stage_all_changes` (used in workflows.py — may not need whitelist)
- `MERGE_BASE_DISTANCE_THRESHOLD` (used in base_branch.py — may not need whitelist)
- `detect_parent_branch_via_merge_base` (used in base_branch.py — may not need whitelist)
- `extract_issue_number_from_branch` (used in base_branch.py — may not need whitelist)
- `get_latest_commit_sha`
- `is_working_directory_clean`
- `get_full_status` (used in workflows.py — may not need whitelist)
- `get_branch_diff` (used in compact_diffs.py — may not need whitelist)
- `validate_branch_name` (used in branches.py — may not need whitelist)

Run vulture after adding exports — only whitelist symbols that actually trigger warnings.

## COMMIT

`feat: expand git_operations __init__.py with 19 new re-exports (#127)`
