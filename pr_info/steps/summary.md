# Summary: list_directory — path, dirs_only, auto-collapsing, truncation

**Issue:** #46

## Goal

Enhance `list_directory()` with `path` and `dirs_only` parameters, plus auto-collapsing and truncation for large listings. All new logic lives in a new `tree_listing.py` module; existing `directory_utils.py` stays unchanged.

## Architectural / Design Changes

### New Module

- **`src/mcp_workspace/file_tools/tree_listing.py`** — Tree building, scoring, collapsing, rendering, truncation. Sits between `list_files()` (raw input) and `list_directory()` (MCP tool).

### Data Flow (before)

```
list_directory() → list_files(".") → flat List[str]
```

### Data Flow (after)

```
list_directory(path, dirs_only)
  → list_files(path)          # raw flat file list (unchanged)
  → list_directory_tree(...)   # NEW: build tree → collapse → render → truncate
  → List[str]                  # same return type
```

### Design Principles

- **One public function** (`list_directory_tree`) — everything else is private (`_TreeNode`, `_build_tree`, `_collapse`, `_render`, `_truncate`)
- **`list_files()` unchanged** — it remains the raw input layer for `search_files` and other callers
- **No new dependencies** — pure Python, stdlib only (dataclasses, pathlib)
- **In-place mutation** for collapsing — simple greedy loop mutates the tree
- **No architecture config changes** — new module is inside existing `file_tools/` package

### Key Data Structure

```python
@dataclass
class _TreeNode:
    name: str
    children: Dict[str, "_TreeNode"]   # subdirectory children
    files: List[str]                    # direct file names
    collapsed: bool = False
    collapsed_file_count: int = 0      # recursive file count when collapsed
```

### Algorithm Summary

1. Build tree from flat file paths (stripping `base_path` prefix internally for tree structure)
2. While line count > 250: score all collapsible dirs (depth ≥ 2), collapse highest-scoring
3. Render to `List[str]` — output paths always include the full project-relative path (base_path is re-added during rendering, so `list_directory(path="src")` returns `["src/a.py", ...]`)
4. If still > 250 entries at root level: truncate with summary line

### Scoring Formula

```
score = (direct_file_count + direct_subdir_count * 0.3) * relative_depth
```

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_workspace/file_tools/tree_listing.py` | Tree building, collapsing, rendering |
| `tests/file_tools/test_tree_listing.py` | Tests for tree listing logic |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/file_tools/__init__.py` | Export `list_directory_tree` |
| `src/mcp_workspace/server.py` | Add `path`/`dirs_only` params to `list_directory()` |

## Files Unchanged

| File | Reason |
|------|--------|
| `src/mcp_workspace/file_tools/directory_utils.py` | Raw input layer — stays as-is |
| `vulture_whitelist.py` | `list_directory` already whitelisted |
| `.importlinter` | `file_tools` package already covered |
| `tach.toml` | `mcp_workspace.file_tools` already covered |

## Implementation Steps

| Step | Description |
|------|-------------|
| [Step 1](step_1.md) | `_TreeNode` dataclass + `_build_tree` + `_render` (basic, no collapsing) |
| [Step 2](step_2.md) | Sorting (dirs first, then files, alphabetical) + `dirs_only` mode |
| [Step 3](step_3.md) | Auto-collapsing: scoring + greedy collapse loop |
| [Step 4](step_4.md) | Truncation after collapsing |
| [Step 5](step_5.md) | Wire into `server.py` — `path` and `dirs_only` parameters on `list_directory()` |
