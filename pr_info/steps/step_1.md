# Step 1: Position-aware duplicate prevention — core fix + tests

**Ref:** [summary.md](summary.md) | Issue #43

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file. Implement the position-aware duplicate prevention for `edit_file`. Follow TDD: write the two core test cases first, verify they fail, then apply the fix to make them pass. Run all three code quality checks (pylint, pytest, mypy) before committing.

## WHERE

- **Modify:** `tests/file_tools/test_edit_file_issues.py` — add 2 test methods to existing `TestEditFileIndentationIssues` class
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
    if (current_content[pos:pos+len(final_new_text)] == final_new_text
            or current_content[pos:pos+len(new_text)] == new_text):
        append skipped result, continue
    
    line_index = ...
    current_content = current_content.replace(...)
```

## ALGORITHM (pseudocode)

```
pos = content.find(old_text)
if content[pos : pos + len(final_new_text)] == final_new_text:
    result = skipped
elif content[pos : pos + len(new_text)] == new_text:
    result = skipped
else:
    proceed with replacement using pos
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
