# fix(edit): position-aware duplicate prevention for substring matches

**Issue:** #43

## Problem

`edit_file` creates duplicate content when `old_text` is a substring/prefix of the actual file content at the match position. The existing `_is_edit_already_applied()` guard only runs when `old_text` is NOT found, so it never catches the case where `old_text` is found but `new_text` is already present at that position.

**Example:** File has `def foo() -> None:  # type: ignore[misc]`, edit replaces `def foo() -> None:` with `def foo() -> None:  # type: ignore[misc]` — result is `def foo() -> None:  # type: ignore[misc]  # type: ignore[misc]` (duplicated suffix).

## Design Change

Add a **position-aware already-applied check** inside the `if old_text in current_content:` branch of `edit_file()`, before performing the replacement. This leverages Python's slice semantics to check if `new_text` already exists at the exact match position:

```python
pos = current_content.find(old_text)
# Python slicing handles bounds naturally — no explicit bounds check needed
if (current_content[pos:pos + len(final_new_text)] == final_new_text
        or current_content[pos:pos + len(new_text)] == new_text):
    # skip — desired state already present at this position
```

The second `or` clause covers `preserve_indentation` mode where `final_new_text` may differ from raw `new_text`. When indentation is off, `final_new_text is new_text` so the second clause is never reached.

**No changes to matching semantics** — substring matching remains intentional. The fix only adds a pre-replacement guard.

## Files to Modify

| File | Action |
|------|--------|
| `src/mcp_workspace/file_tools/edit_file.py` | Add position-aware check in the match branch; reuse `find()` position |
| `tests/file_tools/test_edit_file_issues.py` | Add 4 test cases for the new behavior |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| [Step 1](step_1.md) | Add tests for position-aware duplicate prevention | Tests + production fix in one commit |
| [Step 2](step_2.md) | Add tests for edge cases (indentation + bounds) | Tests + verify existing code handles them |
