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

### 6. Update code comments

Update the distance-counting comments to reflect the new direction:
- Line ~77: `# Count commits from merge-base to branch HEAD` → `# Count commits from merge-base to current HEAD`
- Line ~133: `# Count commits from merge-base to remote branch HEAD` → `# Count commits from merge-base to current HEAD`

### 7. Update function docstring

The docstring (around lines 24-35) describes the old algorithm direction. Change:
- `"The parent is the branch whose HEAD is closest to the merge-base (smallest distance)."` → `"The parent is the branch whose merge-base is closest to the current HEAD (smallest distance)."`

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

### `test_simple_branch_from_main` (line ~72)

Change `mock_repo.iter_commits.return_value = iter([])` to `mock_repo.iter_commits.return_value = []`. The `iter([])` creates a one-shot iterator that can only be consumed once — after removing early-exit, using a reusable list is safer.

### `test_branch_from_feature_branch` (line ~100)

This test's mock needs no changes — `featureA456` is the merge-base hexsha which appears in both old and new rev_range formats.

### `test_multiple_candidates_pick_smallest` (line ~196)

Same analysis: `"featureA456" in rev_range` checks the merge-base hexsha `"mbA"` vs `"mbDevelop"`. Wait — this test uses `merge_base_a.hexsha = "mbA"`. The old range was `"mbA..featureA456"`, so `"featureA456" in rev_range` matched. The new range is `"mbA..current123"` — `"featureA456"` is **no longer in the string**.

**Fix**: change the check to match on the merge-base hexsha:
```python
def mock_iter_commits(rev_range: str) -> list[MagicMock]:
    if "mbA" in rev_range:           # merge-base for feature-A
        return [MagicMock() for _ in range(3)]
    return [MagicMock() for _ in range(8)]  # merge-base for develop
```

### Patch `get_default_branch_name`

Add a class-scoped autouse fixture inside `TestDetectParentBranchViaMergeBase` that patches `get_default_branch_name` with `return_value=None`. This applies to all test methods without changing their signatures.

```python
@pytest.fixture(autouse=True)
def _patch_get_default_branch(self) -> Generator[MagicMock, None, None]:
    with patch(
        "mcp_workspace.git_operations.parent_branch_detection.get_default_branch_name",
        return_value=None,
    ) as mock_default:
        yield mock_default
```

Per-test `@patch` decorators in step 2 override this default where tiebreaker behavior matters.

## DATA

No changes to return types or signatures. `detect_parent_branch_via_merge_base` still returns `Optional[str]`.

## Commit

```
fix: reverse merge-base distance direction and remove early-exit
```
