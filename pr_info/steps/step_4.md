# Step 4: Truncation after collapsing

**Summary:** [summary.md](summary.md)

## LLM Prompt

> Implement Step 4 of the plan in `pr_info/steps/step_4.md`.
> Read the summary at `pr_info/steps/summary.md` for full context.
> Follow TDD: write tests first, then implement, then run all checks.

## Goal

After collapsing, if the root level still exceeds 250 entries, truncate and append a summary line.

## WHERE

- **Modify:** `src/mcp_workspace/file_tools/tree_listing.py` — add `_truncate`; update `list_directory_tree`
- **Modify:** `tests/file_tools/test_tree_listing.py` — add truncation tests

## WHAT

```python
def _truncate(lines: List[str], limit: int = _COLLAPSE_THRESHOLD) -> List[str]:
    """If lines exceed limit, keep first `limit` entries and append summary."""
```

Update `list_directory_tree` to call `_truncate` after rendering.

## ALGORITHM

### `_truncate`

```
if len(lines) <= limit:
    return lines
# Lines are already sorted (dirs first, files second) from _render
kept = lines[:limit]
remaining = lines[limit:]
remaining_dirs = count entries ending with "/" or matching collapsed pattern
remaining_files = len(remaining) - remaining_dirs
total = len(lines)
summary = f"... and {len(remaining)} more entries ({remaining_dirs} dirs, {remaining_files} files) — {total} total"
return kept + [summary]
```

### Classifying truncated entries

A line is a "dir" entry if:
- It ends with `"/"`, OR
- It matches the collapsed pattern `".../ (N files)"` (contains `"/ ("`)

Everything else is a "file" entry.

### `list_directory_tree` update

```
tree = _build_tree(file_paths, base_path)
_collapse(tree, dirs_only)
render_prefix = "" if base_path in (".", "") else base_path.rstrip("/") + "/"
lines = _render(tree, prefix=render_prefix, dirs_only=dirs_only)
return _truncate(lines)
```

## DATA

**Truncation summary format:**
```
... and 50 more entries (10 dirs, 40 files) — 300 total
```

## TESTS

1. **No truncation** — ≤ 250 lines → no summary appended
2. **Truncation triggers** — > 250 lines → exactly 251 entries (250 + summary)
3. **Summary line format** — matches `"... and N more entries (X dirs, Y files) — Z total"`
4. **Dir/file counts in summary** — correctly distinguishes dirs vs files in truncated portion
5. **Truncation preserves sort order** — dirs first, so truncated entries are mostly files
6. **Truncation in dirs_only mode** — same limit applies, summary counts are all dirs

## DONE WHEN

- Output never exceeds 251 lines (250 entries + optional summary)
- Summary line accurately reports what was truncated
- Works in both default and `dirs_only` modes
- pylint, mypy, pytest all green
