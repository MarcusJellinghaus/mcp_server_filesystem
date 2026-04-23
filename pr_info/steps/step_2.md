# Step 2: Edge case tests — indentation + bounds

**Ref:** [summary.md](summary.md) | Issue #43

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file. Add the two edge case tests to `test_edit_file_issues.py`. These should pass against the fix from Step 1 without additional production code changes. Run all three code quality checks (pylint, pytest, mypy) before committing.

## WHERE

- **Modify:** `tests/file_tools/test_edit_file_issues.py` — add 2 test methods to existing `TestEditFileIndentationIssues` class

## WHAT — Tests

### Test 3: `test_prefix_match_skipped_with_preserve_indentation`

Verifies the duplicate check works when `preserve_indentation` is enabled.

- **Setup:** File contains `    return value  # validated` (4-space indent)
- **Edit:** `old_text="    return value"` → `new_text="return value  # validated"`, `options={"preserve_indentation": True}`
- **Why this works:** `preserve_indentation` detects that `new_text` has no indent but `old_text` does, so it prepends 4 spaces → `final_new_text="    return value  # validated"`. The position check catches that this already matches at the match position.
- **Assert:** Result has `match_type: "skipped"`, file content unchanged

### Test 4: `test_new_text_longer_than_remaining_content_proceeds`

Ensures no false skip when `new_text` extends beyond end of file from match position.

- **Setup:** File contains exactly `short` (no trailing newline, 5 chars)
- **Edit:** `old_text="short"` → `new_text="short_with_much_longer_suffix"`
- **Why this works:** `content[0:28]` with only 5 chars returns `"short"` which != `"short_with_much_longer_suffix"`, so the guard doesn't trigger.
- **Assert:** Result has `match_type: "exact"`, file contains `short_with_much_longer_suffix`

## DATA

No new data structures. Tests verify existing result shapes from Step 1's implementation.

## ALGORITHM

No new production code. Both tests validate the existing guard from Step 1:
- Test 3 exercises the `or current_content[pos:pos+len(new_text)] == new_text` clause
- Test 4 exercises that Python's slice semantics naturally handle bounds (no explicit check needed)
