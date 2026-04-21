# Step 1: Fix algorithm + update existing tests

> **Context:** Read `pr_info/steps/summary.md` first for full background.

## Goal

Port the mcp_coder PR #873 algorithm fix into mcp_workspace and update the 2 existing tests whose mocks break due to the changed `iter_commits` range direction.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_workspace/git_operations/parent_branch_detection.py` | Modify |
| `tests/git_operations/test_parent_branch_detection.py` | Modify |

## WHAT — Production code changes

### 1. Add import (line ~12)

```python
from .branch_queries import get_default_branch_name
```

### 2. Call `get_default_branch_name` once at the top of the function

Inside the `with safe_repo_context(project_dir) as repo:` block, before the branch loops:

```python
default_branch = get_default_branch_name(project_dir)
```

### 3. Reverse distance direction (both loops)

**Local loop** — change:
```python
f"{merge_base.hexsha}..{branch.commit.hexsha}"
```
to:
```python
f"{merge_base.hexsha}..{current_commit.hexsha}"
```

**Remote loop** — change:
```python
f"{merge_base.hexsha}..{ref.commit.hexsha}"
```
to:
```python
f"{merge_base.hexsha}..{current_commit.hexsha}"
```

### 4. Remove both early-exit blocks

Delete both instances of:
```python
if distance == 0:
    logger.debug(...)
    return branch.name  # (or branch_name for remote)
```

Keep the `if distance <= distance_threshold:` append logic — distance=0 candidates now flow into `candidates_passing` naturally.

### 5. Add tiebreaker to sort

Change:
```python
candidates_passing.sort(key=lambda x: x[1])
```
to:
```python
candidates_passing.sort(key=lambda x: (x[1], 0 if x[0] == default_branch else 1))
```

## ALGORITHM (pseudocode)

```
default_branch = get_default_branch_name(project_dir)
for each candidate branch:
    merge_base = repo.merge_base(current_commit, candidate_commit)
    distance = count(commits from merge_base to current_commit)  # FIXED direction
    if distance <= threshold: collect (name, distance)            # no early exit
sort by (distance, 0 if default_branch else 1)                   # tiebreaker
return first candidate or None
```

## WHAT — Existing test updates

Only 2 tests need changes — those using `side_effect` on `iter_commits` that inspect the rev_range string:

### `test_branch_from_feature_branch` (line ~100)

The `mock_iter_commits` currently checks `"featureA456" in rev_range` (candidate hexsha). After the fix, the range always ends with `current123` (current branch hexsha). Fix: distinguish by **merge-base hexsha** instead.

```python
def mock_iter_commits(rev_range: str) -> list[MagicMock]:
    if "featureA456" in rev_range:  # merge-base for feature-A = featureA456
        return []  # 0 commits from merge-base to current
    return [MagicMock() for _ in range(15)]  # 15 commits
```

This still works because `merge_base_feature_a.hexsha = "featureA456"` and `merge_base_main.hexsha = "oldmain000"`. The range becomes `"featureA456..current123"` vs `"oldmain000..current123"` — so checking for `"featureA456"` still matches correctly. **No change needed to this test's mock.**

Actually — re-checking: the rev_range was `merge_base..candidate` before, now it's `merge_base..current`. The `"featureA456" in rev_range` check matches the merge-base hexsha (which is `"featureA456"`), so it still matches. **This test needs no mock changes**, only the semantic comment update.

### `test_multiple_candidates_pick_smallest` (line ~196)

Same analysis: `"featureA456" in rev_range` checks the merge-base hexsha `"mbA"` vs `"mbDevelop"`. Wait — this test uses `merge_base_a.hexsha = "mbA"`. The old range was `"mbA..featureA456"`, so `"featureA456" in rev_range` matched. The new range is `"mbA..current123"` — `"featureA456"` is **no longer in the string**.

**Fix**: change the check to match on the merge-base hexsha:
```python
def mock_iter_commits(rev_range: str) -> list[MagicMock]:
    if "mbA" in rev_range:           # merge-base for feature-A
        return [MagicMock() for _ in range(3)]
    return [MagicMock() for _ in range(8)]  # merge-base for develop
```

Also add a `get_default_branch_name` patch (returning `None`) to both tests that have multiple candidates, since the function now calls it. Or better: patch it once at the class level with a default return of `None`.

### Patch `get_default_branch_name`

Add a class-level patch so the production code doesn't call the real function during tests:

```python
@patch("mcp_workspace.git_operations.parent_branch_detection.get_default_branch_name", return_value=None)
```

This can go on each test method that needs it, or as a class-level autouse fixture. Per the issue constraints: **do not add to the shared `mock_repo` fixture**. A class-level `@patch` decorator is the simplest approach — it applies to all methods but doesn't touch the fixture.

## DATA

No changes to return types or signatures. `detect_parent_branch_via_merge_base` still returns `Optional[str]`.

## Commit

```
fix: reverse merge-base distance direction and remove early-exit
```
