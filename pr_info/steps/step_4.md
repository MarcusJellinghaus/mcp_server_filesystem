# Step 4: Add `Merge Status:` line to formatters + tests

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 4: add the
> `Merge Status:` display line to both `format_for_human()` and `format_for_llm()`.
> Write tests first in `test_branch_status_pr_fields.py`, then implement. Run all checks after.

## WHERE

- `src/mcp_workspace/checks/branch_status.py` — modify `format_for_human()`, `format_for_llm()`
- `tests/checks/test_branch_status_pr_fields.py` — add merge status test classes

## WHAT

### Human formatter (`format_for_human`)

Add `Merge Status:` line immediately after the PR line, inside the `if self.pr_found` block:

```python
if self.pr_found is not None:
    if self.pr_found:
        lines.append(f"PR: ✅ #{self.pr_number} ({self.pr_url})")
        # NEW: Merge Status line
        if self.pr_mergeable is True:
            lines.append("Merge Status: ✅ Mergeable (squash-merge safe)")
        elif self.pr_mergeable is False:
            lines.append("Merge Status: ❌ Not mergeable (has conflicts)")
        else:
            lines.append("Merge Status: ⏳ Pending")
    else:
        lines.append("PR: ❌ No PR found")
    lines.append("")
```

Decision: `Merge Status:` only appears when a PR is found (`pr_found=True`).
When `pr_found=False` or `pr_found=None`, omit entirely.

### LLM formatter (`format_for_llm`)

Add `Mergeable=` token to the status summary line:

```python
if self.pr_found is True:
    mergeable_str = str(self.pr_mergeable) if self.pr_mergeable is not None else "None"
    status_summary += f", PR=#{self.pr_number}, Mergeable={mergeable_str}"
elif self.pr_found is False:
    status_summary += ", PR=NOT_FOUND"
```

## DATA

Display values (human format):
- `pr_mergeable=True` → `"Merge Status: ✅ Mergeable (squash-merge safe)"`
- `pr_mergeable=False` → `"Merge Status: ❌ Not mergeable (has conflicts)"`
- `pr_mergeable=None` → `"Merge Status: ⏳ Pending"`
- No PR → line omitted

Display values (LLM format):
- `pr_mergeable=True` → `"Mergeable=True"` in status summary
- `pr_mergeable=False` → `"Mergeable=False"` in status summary
- `pr_mergeable=None` → `"Mergeable=None"` in status summary
- No PR → omitted

## TEST CHANGES in `test_branch_status_pr_fields.py`

Update `_make_report` helper to accept `pr_mergeable` parameter.

Add `TestMergeStatusInHumanFormat`:
1. `test_mergeable_true` — assert "Mergeable (squash-merge safe)" in output
2. `test_mergeable_false` — assert "Not mergeable (has conflicts)" in output
3. `test_mergeable_none` — assert "Pending" in output
4. `test_no_pr_omits_merge_status` — `pr_found=False`, assert "Merge Status" not in output
5. `test_pr_none_omits_merge_status` — `pr_found=None`, assert "Merge Status" not in output

Add `TestMergeStatusInLLMFormat`:
1. `test_mergeable_true` — assert "Mergeable=True" in output
2. `test_mergeable_false` — assert "Mergeable=False" in output
3. `test_mergeable_none` — assert "Mergeable=None" in output
4. `test_no_pr_omits_mergeable` — `pr_found=False`, assert "Mergeable=" not in output
