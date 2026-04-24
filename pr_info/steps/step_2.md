# Step 2: Sorting + dirs_only mode

**Summary:** [summary.md](summary.md)

## LLM Prompt

> Implement Step 2 of the plan in `pr_info/steps/step_2.md`.
> Read the summary at `pr_info/steps/summary.md` for full context.
> Follow TDD: write tests first, then implement, then run all checks.

## Goal

Add deterministic sort order (directories first, then files, both alphabetical at every level) and implement `dirs_only=True` mode that shows only directories with trailing `/`.

## WHERE

- **Modify:** `src/mcp_workspace/file_tools/tree_listing.py` — update `_render`
- **Modify:** `tests/file_tools/test_tree_listing.py` — add sorting + dirs_only tests

## WHAT

Update `_render` to:
1. Sort children dirs alphabetically, sort files alphabetically
2. Emit dirs before files at every level
3. When `dirs_only=True`: emit directory paths with trailing `/`, skip files

### Rendering rules (from issue)

| Mode | Expanded dirs shown? | Files shown? |
|------|---------------------|-------------|
| `dirs_only=False` (default) | No (dirs are implicit in file paths) | Yes |
| `dirs_only=True` | Yes, with trailing `/` | No |

## ALGORITHM

### `_render` (updated)

```
results = []
sorted_children = sorted(node.children.keys())
sorted_files = sorted(node.files)
for dir_name in sorted_children:
    child = node.children[dir_name]
    if dirs_only:
        append prefix + dir_name + "/"
    recurse into child with prefix + dir_name + "/"
if not dirs_only:
    for filename in sorted_files:
        append prefix + filename
return results
```

## DATA

**Input:** `["z.py", "a.py", "tests/b.py", "src/x.py", "src/a.py"]`

**Output (dirs_only=False):**
```
["src/a.py", "src/x.py", "tests/b.py", "a.py", "z.py"]
```
(dirs first at root: src/, tests/ contents before root files a.py, z.py)

**Output (dirs_only=True):**
```
["src/", "tests/"]
```

## TESTS

1. **Sort order** — dirs before files, alphabetical within each group, at every nesting level
2. **dirs_only=True basic** — only directories shown, each with trailing `/`
3. **dirs_only=True nested** — nested dirs shown: `"src/"`, `"src/utils/"`
4. **dirs_only=True no files** — files completely excluded
5. **dirs_only=False unchanged** — default mode still produces file paths only (no dir lines)
6. **Mixed depth sorting** — verify sort applies at every level, not just root

## DONE WHEN

- Output is deterministically sorted (dirs first, alphabetical)
- `dirs_only=True` shows only directory paths with trailing `/`
- `dirs_only=False` behavior unchanged from Step 1 (except now sorted)
- pylint, mypy, pytest all green
