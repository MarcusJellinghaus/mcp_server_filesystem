# Step 1: _TreeNode + _build_tree + _render (basic listing)

**Summary:** [summary.md](summary.md)

## LLM Prompt

> Implement Step 1 of the plan in `pr_info/steps/step_1.md`.
> Read the summary at `pr_info/steps/summary.md` for full context.
> Follow TDD: write tests first, then implement, then run all checks.

## Goal

Create the `tree_listing.py` module with the core tree data structure, tree building from flat file paths, and basic rendering to `List[str]`. No collapsing or truncation yet — just build a tree and render it back to the same flat file list that `list_files()` produces.

## WHERE

- **Create:** `src/mcp_workspace/file_tools/tree_listing.py`
- **Create:** `tests/file_tools/test_tree_listing.py`
- **Modify:** `src/mcp_workspace/file_tools/__init__.py` — add export

## WHAT

### `tree_listing.py`

```python
from dataclasses import dataclass, field
from typing import Dict, List

_COLLAPSE_THRESHOLD = 250

@dataclass
class _TreeNode:
    name: str
    children: Dict[str, "_TreeNode"] = field(default_factory=dict)
    files: List[str] = field(default_factory=list)
    collapsed: bool = False
    collapsed_file_count: int = 0

def _build_tree(file_paths: List[str], base_path: str) -> _TreeNode:
    """Build tree from flat file paths. base_path is stripped from each path prefix."""

def _render(node: _TreeNode, prefix: str, dirs_only: bool) -> List[str]:
    """Render tree to flat list of path strings (no sorting yet)."""

def list_directory_tree(file_paths: List[str], base_path: str = ".", dirs_only: bool = False) -> List[str]:
    """Public API: build tree, render to list. Collapsing/truncation added in later steps."""
```

### `__init__.py` addition

```python
from mcp_workspace.file_tools.tree_listing import list_directory_tree
```

Add `"list_directory_tree"` to `__all__`.

## ALGORITHM

### `_build_tree`

```
create root node with name=""
for each file_path in file_paths:
    strip base_path prefix (if not ".")
    split remaining path into parts
    walk/create child nodes for directory parts
    add filename to leaf node's files list
return root
```

### `_render` (basic, no collapsing logic yet)

```
results = []
for each child dir in node.children:
    recurse into child, prepending prefix + child.name + "/"
for each file in node.files:
    append prefix + filename
return results
```

### `list_directory_tree`

```
tree = _build_tree(file_paths, base_path)
return _render(tree, prefix="", dirs_only=False)
```

## DATA

- **Input:** `["src/a.py", "src/b.py", "tests/test_a.py"]`
- **Output (dirs_only=False):** `["src/a.py", "src/b.py", "tests/test_a.py"]`
- The output is the same paths as input (just rebuilt through the tree). Order doesn't matter yet — sorting is Step 2.

## TESTS (`test_tree_listing.py`)

1. **Empty input** → returns `[]`
2. **Flat files only** (no subdirs) → returns same files
3. **Nested structure** → all paths preserved through tree round-trip
4. **base_path stripping** — input paths like `"src/utils/a.py"` with `base_path="src"` produce `"utils/a.py"`
5. **Deeply nested** — `"a/b/c/d/file.txt"` round-trips correctly

## DONE WHEN

- Tests pass
- `list_directory_tree` round-trips flat file paths through tree and back
- pylint, mypy, pytest all green
