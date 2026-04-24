# Step 3: Auto-collapsing — scoring + greedy collapse loop

**Summary:** [summary.md](summary.md)

## LLM Prompt

> Implement Step 3 of the plan in `pr_info/steps/step_3.md`.
> Read the summary at `pr_info/steps/summary.md` for full context.
> Follow TDD: write tests first, then implement, then run all checks.

## Goal

Implement auto-collapsing: when rendered output exceeds 250 lines, greedily collapse directories to fit within budget. Depth-1 directories are hard-protected and never collapsed.

## WHERE

- **Modify:** `src/mcp_workspace/file_tools/tree_listing.py` — add `_count_lines`, `_score`, `_find_collapsible`, `_recursive_file_count`, `_collapse`; update `_render` and `list_directory_tree`
- **Modify:** `tests/file_tools/test_tree_listing.py` — add collapsing tests

## WHAT

```python
def _count_lines(node: _TreeNode, dirs_only: bool) -> int:
    """Count how many output lines the tree would produce."""

def _recursive_file_count(node: _TreeNode) -> int:
    """Count all files recursively under a node (post-collapse)."""

def _score(node: _TreeNode, depth: int) -> float:
    """Score = (len(files) + len(children) * 0.3) * depth"""

def _find_collapsible(node: _TreeNode, depth: int) -> List[Tuple[float, _TreeNode]]:
    """Find all collapsible directories (depth >= 2, not already collapsed)."""

def _collapse(root: _TreeNode, dirs_only: bool) -> None:
    """Greedy loop: while line_count > 250, collapse highest-scoring dir. Mutates tree."""
```

Update `_render` to handle collapsed nodes:
- When `node.collapsed is True`, emit `"dir_name/ (N files)"` instead of recursing
- If `collapsed_file_count == 0`, emit just `"dir_name/"`

## ALGORITHM

### `_collapse`

```
while _count_lines(root, dirs_only) > _COLLAPSE_THRESHOLD:
    candidates = _find_collapsible(root, depth=1)
    if not candidates:
        break  # nothing left to collapse (edge case: root has only files)
    pick candidate with highest score (break ties by name for determinism)
    candidate.collapsed = True
    candidate.collapsed_file_count = _recursive_file_count(candidate)
    candidate.children.clear()
    candidate.files.clear()
```

### `_count_lines`

```
count = 0
if node.collapsed: return 1
for child in children: count += _count_lines(child, dirs_only)
if dirs_only: count += len(children)  # each expanded dir is a line
else: count += len(files)              # each file is a line
return count
```

### `_find_collapsible`

```
results = []
for child in node.children.values():
    if depth >= 2 and not child.collapsed:
        results.append((score(child, depth), child))
    results.extend(_find_collapsible(child, depth + 1))
return results
```

### `_render` update for collapsed nodes

```
for dir_name in sorted_children:
    child = node.children[dir_name]
    if child.collapsed:
        if child.collapsed_file_count > 0:
            append prefix + dir_name + "/ (" + count + " files)"
        else:
            append prefix + dir_name + "/"
    else:
        # existing render logic (recurse)
```

### Scoring

```
score = (len(node.files) + len(node.children) * 0.3) * depth
```

- `files` and `children` are **direct** counts only
- `depth` is relative to listed path (root's children are depth 1)

### Rules

- Depth-1 directories (immediate children of root) are **never collapsed**
- Collapsed directory replaces entire subtree
- Parent scores do NOT change after child collapse
- Edge case: root with only files and no subdirs → show everything (nothing to collapse)

## DATA

**Collapsed line format:**
- `"git_operations/ (18 files)"` — when recursive file count > 0
- `"empty_pkg/"` — when recursive file count is 0

Same format in both `dirs_only=False` and `dirs_only=True`.

## TESTS

1. **No collapsing needed** — < 250 lines → output unchanged from Step 2
2. **Collapsing triggers** — create tree with > 250 lines, verify output ≤ 250
3. **Depth-1 protection** — depth-1 dirs never appear as collapsed summaries
4. **Collapsed line format** — verify `"dirname/ (N files)"` format
5. **Collapsed format zero files** — verify `"dirname/"` when empty
6. **Deeper dirs collapsed first** — depth-3 dir collapses before depth-2 with same content
7. **Scoring prefers file-heavy dirs** — dir with 10 files collapses before dir with 10 subdirs
8. **Root with only files** — no dirs to collapse → all files shown regardless of count
9. **Collapsing applies to dirs_only mode too** — same behavior with `dirs_only=True`
10. **Collapsed file count is recursive** — collapsing a dir with nested subdirs counts all files

## DONE WHEN

- Trees exceeding 250 lines are collapsed to ≤ 250
- Depth-1 dirs always visible
- Scoring formula matches spec
- Collapsed line format correct
- pylint, mypy, pytest all green
