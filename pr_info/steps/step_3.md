# Step 3: Migrate Remaining Test Files

## Context

Read `pr_info/steps/summary.md` for the full picture. Steps 1-2 are complete — the
utility and server tool have been rewritten. This step migrates the 3 remaining test
files to the new interface.

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file. Steps 1-2 are complete.
> Migrate the 3 remaining test files to the new `edit_file` interface. Preserve the
> regression scenarios — the *what* being tested stays, only the *how* (call
> signature and assertions) changes. Run all quality checks after. Commit as one unit.

## WHERE

- `tests/file_tools/test_edit_file_issues.py` — regression tests
- `tests/file_tools/test_edit_already_applied_fix.py` — already-applied detection tests
- `tests/file_tools/test_edit_file_backslash.py` — backslash hint tests

## WHAT — Migration rules (apply to all 3 files)

| Before | After |
|--------|-------|
| `edit_file(path, [{"old_text": ..., "new_text": ...}])` | `edit_file(path, old_string=..., new_string=...)` |
| `result["success"]` is True | No exception raised |
| `result["success"]` is False | `ValueError` raised |
| `result["diff"]` non-empty | Return value is a non-empty string containing diff markers |
| `result["diff"] == ""` | Return value is a plain message string (no `---`/`+++`) |
| `result["message"]` | Return value is the message string |
| `result["error"]` | `ValueError` message |
| `result["match_results"][i]["match_type"] == "skipped"` | Return value is message string |
| `result["match_results"][i]["match_type"] == "failed"` | `ValueError` raised |
| `options={"preserve_indentation": True}` | Remove — feature deleted |

## WHAT — test_edit_file_issues.py changes

### Tests to keep (adapt signature + assertions)
- `test_extreme_indentation_handling` — indentation fix still works
- `test_optimization_edit_already_applied` — already-applied detection
- `test_false_positive_already_applied_bug_fix` — false positive prevention
- `test_first_occurrence_replacement` — first occurrence only (now also test that multiple matches raise without `replace_all`)
- `test_prefix_match_does_not_create_duplicates` — position-aware already-applied check
- `test_legitimate_prefix_replacement_proceeds` — valid edit goes through
- `test_new_text_longer_than_remaining_content_proceeds` — edge case

### Tests to remove
- `test_normalize_line_endings` — move to test_edit_file.py or keep here (it tests a utility, not edit_file)
- `test_basic_indentation_preservation` — `preserve_indentation` removed
- `test_snake_case_options` — `options` parameter removed
- `test_prefix_match_skipped_with_preserve_indentation` — `preserve_indentation` removed

## WHAT — test_edit_already_applied_fix.py changes

### Tests to keep (adapt signature + assertions)
- `test_is_edit_already_applied_helper_function` — tests `_is_edit_already_applied` directly, unchanged
- `test_false_positive_prevention_single_line` — adapt to string return
- `test_false_positive_prevention_multiline` — adapt to string return
- `test_legitimate_already_applied_detection` — adapt to string return
- `test_complex_false_positive_scenario` — adapt to string return

### Tests to remove
- `test_false_positive_with_preserve_indentation` — `preserve_indentation` removed

## WHAT — test_edit_file_backslash.py changes

### Test to keep (adapt signature + assertions)
- `test_single_backslash_old_text_gives_hint` — now expects `ValueError` raised with hint in message instead of error dict

## DATA — Assertion patterns

```python
# Success: returns diff string
result = edit_file(path, old_string="old", new_string="new")
assert "---" in result  # it's a diff

# Already applied: returns message string
result = edit_file(path, old_string="old", new_string="new")
assert "No changes needed" in result

# Failure: raises ValueError
with pytest.raises(ValueError, match="not found"):
    edit_file(path, old_string="missing", new_string="new")

# Backslash hint: ValueError message contains hint
with pytest.raises(ValueError, match="double backslashes"):
    edit_file(path, old_string=single_bs, new_string="new")
```

## Decisions

- `test_normalize_line_endings` stays in `test_edit_file_issues.py` — it's a standalone utility test, moving it would be churn
- All files keep `unittest.TestCase` style where they already use it
- Regression scenario logic is preserved 1:1 — only the assertion mechanism changes
