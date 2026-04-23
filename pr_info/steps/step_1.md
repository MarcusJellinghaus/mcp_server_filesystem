# Step 1: Position-aware duplicate prevention — core fix + all tests

**Ref:** [summary.md](summary.md) | Issue #43

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file. Implement the position-aware duplicate prevention for `edit_file`. Follow TDD: write the four test cases first, verify the first two fail, then apply the fix to make all pass. Run all three code quality checks (pylint, pytest, mypy) before committing.

## WHERE

- **Modify:** `tests/file_tools/test_edit_file_issues.py` — add 4 test methods to existing `TestEditFileIndentationIssues` class
- **Modify:** `src/mcp_workspace/file_tools/edit_file.py` — add position-aware check in the `if old_text in current_content:` branch (around line 118)

## WHAT — Tests

### Test 1: `test_prefix_match_does_not_create_duplicates`

Reproduces the exact bug from the issue.

- **Setup:** File contains `def mock_config_path(self, ...) -> None:  # type: ignore[misc]`
- **Edit:** `old_text="def mock_config_path(self, ...) -> None:"` → `new_text="def mock_config_path(self, ...) -> None:  # type: ignore[misc]"`
- **Assert:** Result has `match_type: "skipped"`, file content unchanged, no `# type: ignore[misc]  # type: ignore[misc]`

### Test 2: `test_legitimate_prefix_replacement_proceeds`

Ensures the guard doesn't block valid edits.

- **Setup:** File contains `foo = 1`
- **Edit:** `old_text="foo"` → `new_text="foobar"`
- **Assert:** Result has `match_type: "exact"`, file contains `foobar = 1`

### Test 3: `test_prefix_match_skipped_with_preserve_indentation`

Verifies the duplicate check works when `preserve_indentation` is enabled.

- **Setup:** File contains `    return value  # validated` (4-space indent)
- **Edit:** `old_text="    return value"` → `new_text="return value  # validated"`, `options={"preserve_indentation": True}`
- **Why this works:** `preserve_indentation` detects that `new_text` has no indent but `old_text` does, so it prepends 4 spaces → `final_new_text="    return value  # validated"`. The position check catches that this already matches at the match position. This exercises the first clause (`final_new_text` check) via the indentation adjustment path.
- **Assert:** Result has `match_type: "skipped"`, file content unchanged

### Test 4: `test_new_text_longer_than_remaining_content_proceeds`

Ensures no false skip when `new_text` extends beyond end of file from match position.

- **Setup:** File contains exactly `short` (no trailing newline, 5 chars)
- **Edit:** `old_text="short"` → `new_text="short_with_much_longer_suffix"`
- **Why this works:** `content[0:28]` with only 5 chars returns `"short"` which != `"short_with_much_longer_suffix"`, so the guard doesn't trigger.
- **Assert:** Result has `match_type: "exact"`, file contains `short_with_much_longer_suffix`

## WHAT — Production Code Change

### In `edit_file()`, inside the `if old_text in current_content:` branch:

**Current flow (lines 118-133):**
```
if old_text in current_content:
    compute final_new_text (with optional indentation)
    old_text_position = current_content.find(old_text)
    line_index = ...
    current_content = current_content.replace(...)
```

**New flow:**
```
if old_text in current_content:
    compute final_new_text (with optional indentation)
    old_text_position = current_content.find(old_text)  # moved up (reused)
    
    # NEW: position-aware already-applied check
    if (current_content[old_text_position:old_text_position+len(final_new_text)] == final_new_text
            or current_content[old_text_position:old_text_position+len(new_text)] == new_text):
        append skipped result, continue
    
    line_index = ...
    current_content = current_content.replace(...)
```

## ALGORITHM (pseudocode)

```
old_text_position = content.find(old_text)
if content[old_text_position : old_text_position + len(final_new_text)] == final_new_text:
    result = skipped
elif content[old_text_position : old_text_position + len(new_text)] == new_text:
    result = skipped
else:
    proceed with replacement using old_text_position
```

## DATA

Skipped result structure (matches existing convention):
```python
{
    "edit_index": i,
    "match_type": "skipped",
    "details": "Edit already applied - content already in desired state"
}
```

## HOW — Integration

- The `find()` call already exists at line 131; move it before the new check and reuse it for `line_index` and `replace()`
- The skipped result uses the same `match_type` and `details` string as the existing already-applied handling in the `else` branch (line 152)
- No new imports, no new functions
