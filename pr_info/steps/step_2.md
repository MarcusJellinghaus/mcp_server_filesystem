# Step 2: Add 4 new regression tests

> **Context:** Read `pr_info/steps/summary.md` first for full background. Step 1 must be complete (algorithm is already fixed).

## Goal

Add 4 new test methods to `TestDetectParentBranchViaMergeBase` that validate the corrected merge-base algorithm. Each test targets a specific behavior that the old buggy code got wrong.

## WHERE

| File | Action |
|------|--------|
| `tests/git_operations/test_parent_branch_detection.py` | Modify — add 4 test methods |

## WHAT — 4 new test methods

All tests go inside the existing `TestDetectParentBranchViaMergeBase` class, using the existing `mock_repo` fixture and `_create_mock_branch` / `_create_mock_remote_ref` helpers.

### Test 1: `test_selects_main_over_dormant_feature_branch`

**Scenario (issue #803 regression):** Current branch was created from `main`. A dormant `feature-old` branch diverged from main long ago. Old algorithm measured distance to candidate HEAD and picked the dormant branch (distance=0 to its own HEAD vs large distance to main's HEAD). New algorithm measures distance to current HEAD and correctly picks `main`.

**Setup:**
- Branches: `current` (hexsha `"cur1"`), `main` (hexsha `"main1"`), `feature-old` (hexsha `"old1"`)
- merge_base(current, main) → `"mb_main"` (recent — close to current)
- merge_base(current, feature-old) → `"mb_old"` (ancient — far from current)
- `iter_commits("mb_main..cur1")` → 2 commits (small distance)
- `iter_commits("mb_old..cur1")` → 18 commits (large distance)
- Patch `get_default_branch_name` → `"main"`

**Assert:** result == `"main"`

### Test 2: `test_prefers_default_branch_on_equal_distance`

**Scenario:** Two candidates (`main` and `develop`) both have distance=3. Default branch (`main`) should win via tiebreaker.

**Setup:**
- Branches: `current`, `main`, `develop` — each with distinct merge-bases
- Both `iter_commits` calls return 3 commits
- Patch `get_default_branch_name` → `"main"`

**Assert:** result == `"main"`

### Test 3: `test_includes_candidate_at_threshold`

**Scenario:** Candidate has distance == `MERGE_BASE_DISTANCE_THRESHOLD` (20). Should be included (`<=`), not excluded.

**Setup:**
- Branches: `current`, `main`
- `iter_commits` returns exactly 20 commits

**Assert:** result == `"main"` (not None)

### Test 4: `test_distance_zero_collects_all_candidates`

**Scenario:** Two candidates (`main` and `develop`) both at distance=0. Old code would early-exit on the first one found. New code collects both and applies tiebreaker.

**Setup:**
- Branches: `current`, `develop`, `main` (in this order — `develop` is iterated first)
- Both distances = 0 (iter_commits returns empty)
- Patch `get_default_branch_name` → `"main"`

**Assert:** result == `"main"` (tiebreaker picks default, not first-found `develop`)

## HOW — Mock strategy

Tests 1, 2, and 4 need `get_default_branch_name` patched. Use `@patch` decorator on each individual test method:

```python
@patch(
    "mcp_workspace.git_operations.parent_branch_detection.get_default_branch_name",
    return_value="main",
)
def test_selects_main_over_dormant_feature_branch(
    self, mock_get_default: MagicMock, mock_repo: MagicMock
) -> None:
```

Test 3 does not need the patch (single candidate, no tiebreaker needed). But since step 1 adds a class-level patch with `return_value=None`, it's already covered.

## DATA

No new return types. All tests assert `Optional[str]` returns from the existing function.

## Commit

```
test: add 4 regression tests for merge-base parent detection
```
