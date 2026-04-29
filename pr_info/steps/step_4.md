# Step 4 — Wire feedback into `BranchStatusReport` + recommendation gating

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`).
> Implement Step 4 only. Follow TDD: extend `tests/checks/test_branch_status_pr_fields.py` and `tests/checks/test_branch_status_recommendations.py` first, then update `branch_status.py`. Run pylint + pytest + mypy and confirm all green. Produce exactly one commit.

## Goal

Wire the data layer (Step 2) and the formatter (Step 3) into `collect_branch_status`. Add three new fields to `BranchStatusReport`, splice the formatted text into both `format_for_human` and `format_for_llm`, and gate `_generate_recommendations` so unresolved feedback blocks "Ready to merge" and replaces it with "Address review comments" when CI passes + tasks complete.

## WHERE

- `src/mcp_workspace/checks/branch_status.py`:
  - Extend `BranchStatusReport` with three fields.
  - Add `_collect_pr_feedback` helper.
  - Update `collect_branch_status` to call it after `_collect_pr_info`.
  - Splice `pr_feedback_text` into both formatters.
  - Update `_generate_recommendations`.
- `tests/checks/test_branch_status_pr_fields.py` — add tests for new fields' rendering and `mergeable_state`.
- `tests/checks/test_branch_status_recommendations.py` — add tests for review-blocking gating.

## WHAT

### Dataclass changes

```python
@dataclass(frozen=True)
class BranchStatusReport:
    ...existing fields...
    pr_mergeable_state: Optional[str] = None
    pr_feedback_text: Optional[str] = None     # already-formatted block from Step 3, or None when not collected
    pr_feedback_blocks_merge: bool = False     # True iff unresolved threads, CHANGES_REQUESTED, or open alerts present
```

### New helper

```python
def _collect_pr_feedback(
    pr_manager: PullRequestManager, pr_number: int
) -> tuple[Optional[str], bool]:
    """Fetch PR feedback and return (formatted_text, blocks_merge).

    Returns (None, False) on total failure (logged at debug level).
    """
```

### Formatter changes

- `format_for_human`: after the existing `Merge Status:` line, if `self.pr_feedback_text` is not None, append a blank line + the text. Include `Mergeable_State` in the human-readable Merge Status section as well (e.g., `Mergeable State: clean`).
- `format_for_llm`: include `Mergeable_State=<value>` in the status summary when `pr_found` and `pr_mergeable_state` is set; if `self.pr_feedback_text` is not None, append a blank line + the text after the recommendations line (and before the `CI Errors:` block when present).

### Exact `Mergeable_State` format in `format_for_llm`

The status summary line must follow the existing comma-separated `Key=Value` style. Append `Mergeable_State=<value>` to the existing PR status line, only when `pr_found is True` and `pr_mergeable_state is not None`. Example:

```
PR=#123, Mergeable=True, Mergeable_State=clean
```

When `pr_mergeable_state` is `None`, the `Mergeable_State=...` segment is omitted entirely (no `Mergeable_State=None` rendering).

### Recommendation logic update

```python
# In _generate_recommendations(report_data):
pr_blocks = report_data.get("pr_feedback_blocks_merge", False)

# Replace existing "Ready to merge" branch with:
ci_ok = ci_status in (CIStatus.PASSED, CIStatus.NOT_CONFIGURED)
if ci_ok and tasks_ok and not rebase_needed:
    if pr_blocks:
        recommendations.append("Address review comments")
    elif pr_mergeable is True:
        recommendations.append("Ready to merge (squash-merge safe)")
    else:
        recommendations.append("Ready to merge")
```

## HOW

- Import `PRFeedback` from `pr_manager` only inside `_collect_pr_feedback` (or at module top — already in the github_operations layer, so no import-linter violation).
- `_collect_pr_feedback` calls `pr_manager.get_pr_feedback(pr_number)`, then `_format_pr_feedback(feedback)`. `blocks_merge = bool(feedback["unresolved_threads"] or feedback["changes_requested"] or feedback["alerts"])`.
- In `collect_branch_status`, only call `_collect_pr_feedback` when `pr_found is True` and `pr_number is not None`.
- Pass `pr_mergeable_state` from `_collect_pr_info` (extend its tuple return to include `pr_mergeable_state`) — or fetch it inline in `collect_branch_status` from the same PR dict (preferred — minimal change to existing helper signatures: extend `_collect_pr_info` to return a 5-tuple).

## ALGORITHM (relevant slice of `collect_branch_status`)

```text
1. ... existing PR info collection ...
2. pr_mergeable_state from _collect_pr_info return
3. if pr_found and pr_number is not None:
       pr_feedback_text, pr_feedback_blocks_merge = _collect_pr_feedback(pr_manager, pr_number)
   else:
       pr_feedback_text, pr_feedback_blocks_merge = None, False
4. report_data["pr_feedback_blocks_merge"] = pr_feedback_blocks_merge
5. recommendations = _generate_recommendations(report_data)
6. return BranchStatusReport(..., pr_mergeable_state=..., pr_feedback_text=..., pr_feedback_blocks_merge=...)
```

## DATA

- `BranchStatusReport` gains 3 fields, all with defaults — fully backward-compatible with existing callers and existing test fixtures.
- `_collect_pr_feedback` returns `tuple[Optional[str], bool]`.
- `_collect_pr_info` extended return signature: `tuple[Optional[int], Optional[str], Optional[bool], Optional[bool], Optional[str]]` — the 5th element is `pr_mergeable_state`. Update the one call site accordingly.

## Tests (write these first)

### `tests/checks/test_branch_status_pr_fields.py` — add a class

- `test_mergeable_state_in_human_format` — when `pr_mergeable_state="clean"`, output contains `"clean"`.
- `test_mergeable_state_in_llm_format` — output contains `"Mergeable_State=clean"`.
- `test_pr_feedback_text_in_human_format` — when `pr_feedback_text="PR Reviews:\n[alert] ..."`, output contains it verbatim.
- `test_pr_feedback_text_in_llm_format` — same.
- `test_pr_feedback_text_none_omits_block` — output contains no `"PR Reviews:"`.

### `tests/checks/test_branch_status_recommendations.py` — add a class

- `test_blocks_ready_to_merge_when_pr_feedback_blocks` — CI passed + tasks complete + `pr_feedback_blocks_merge=True` → `"Address review comments"` in recs and `"Ready to merge"` not in recs.
- `test_no_review_rec_when_ci_failed` — CI failed + `pr_feedback_blocks_merge=True` → `"Fix CI test failures"` in recs and `"Address review comments"` NOT in recs (CI takes precedence — issue decision #6).
- `test_no_review_rec_when_tasks_blocking` — tasks incomplete + `pr_feedback_blocks_merge=True` → `"remaining tasks"` in recs and `"Address review comments"` NOT in recs.
- `test_ready_to_merge_when_feedback_clean` — CI passed + tasks complete + `pr_feedback_blocks_merge=False` → `"Ready to merge"` in recs.
- `test_feedback_blocks_take_precedence_over_rebase_and_mergeable` — `rebase_needed=True`, `pr_mergeable=True`, `pr_feedback_blocks_merge=True` (CI passed + tasks complete) → `"Address review comments"` in recs; `"Ready to merge"` and `"Ready to merge (squash-merge safe)"` NOT in recs. Verifies feedback-blocking takes priority within `_generate_recommendations` regardless of rebase/mergeable inputs — the override path is exercised separately at the integration level.

### Existing tests

- All existing tests in `tests/checks/test_branch_status*.py` remain green because new fields have defaults.

## Exit criteria

- pylint passes
- mypy passes (`Optional[str]` and `bool` field annotations correct; `_collect_pr_info` 5-tuple consistent)
- pytest passes (new and existing tests green)
- One commit on the branch
