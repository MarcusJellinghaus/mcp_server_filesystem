# Step 5: Restore branch_status Recommendations, Formats, and Safety

**Commit**: `fix: restore branch_status recommendations and output formats`

## Context
See [summary.md](summary.md) for full issue context.
This step fixes recommendations generation, output formatting, and adds the outer
safety net to `collect_branch_status`. This is the final step.

## LLM Prompt
> Read `pr_info/steps/summary.md` and this file. Fix `_generate_recommendations`,
> `format_for_human`, `format_for_llm`, and `collect_branch_status` in
> `src/mcp_workspace/checks/branch_status.py` as described below.
> Update all affected tests. Run all quality checks.
> Reference project `p_coder` at `src/mcp_coder/checks/branch_status.py` is the source of truth.

## WHERE

| File | Action |
|------|--------|
| `tests/checks/test_branch_status.py` | Update recommendation + format + safety tests |
| `tests/checks/test_branch_status_pr_fields.py` | Update format assertions |
| `src/mcp_workspace/checks/branch_status.py` | Fix 4 areas |

## WHAT

### 1. `_generate_recommendations(report_data) -> List[str]`

**Bug**: Lost `tasks_is_blocking` and `ci_details` parameters. Lost "Ready to merge" /
"Continue with current work" recommendations. Lost gating of rebase recommendation on task status.
Also, the proposed individual-kwargs signature doesn't match p_coder.

**Fix**: Port back the exact logic from p_coder reference project
`src/mcp_coder/checks/branch_status.py` function `_generate_recommendations`. It takes
a single `report_data: Dict[str, Any]` parameter and extracts values from the dict.
Port back all recommendation cases including: `NOT_CONFIGURED` → "Configure CI pipeline",
`ci_details` → "Check CI error details above", task blocking logic, and positive
"Ready to merge"/"Continue with current work" recommendations.

Use `mcp__workspace__read_reference_file` to read the exact implementation.

**Update caller** in `collect_branch_status` to pass the report data dict.

**Tests to update**:
- `test_all_good` → now expects `["Ready to merge"]` (not `[]`)
- Add test: all good with N_A tasks → expects `["Continue with current work"]`
- Add test: rebase needed but tasks blocking → rebase NOT recommended
- Add test: `NOT_CONFIGURED` CI → "Configure CI pipeline"
- Update `test_multiple_issues` for new signature

### 2. `format_for_human()` — restore icon-based output

**Fix**: Port back the exact logic from p_coder reference project
`src/mcp_coder/checks/branch_status.py` method `format_for_human`. Key structural
differences from the current mcp-workspace implementation:

- Includes "Branch Status Report" heading
- Uses "CI Status:" (not "CI:")
- Uses "Rebase Status:" with "UP TO DATE"/"BEHIND" text
- Uses "Task Tracker:" with status text
- Uses "GitHub Status:" label
- Includes PR found/not-found states (p_coder shows "No PR found", not absent)
- Check the p_coder reference for exact icon mappings (e.g., `NOT_CONFIGURED` maps to
  gear icon, `N_A` tasks have conditional blocking logic)

Use `mcp__workspace__read_reference_file` to read the exact implementation. Do NOT use
the simplified pseudocode that was previously here.

**Tests to update**: Assertions in `test_format_for_human` and `test_branch_status_pr_fields.py`
to check for p_coder format.

### 3. `format_for_llm()` — restore compact format

**Fix**: Port back the exact logic from p_coder reference project
`src/mcp_coder/checks/branch_status.py` method `format_for_llm`. P_coder uses a compact
single-line summary format (`"Branch: X | Base: Y"`, `"Branch Status: CI=..., Rebase=...,
Tasks=..."`), NOT the markdown bullet format currently in mcp-workspace.

Use `mcp__workspace__read_reference_file` to read the exact implementation.

**Tests to update**: All LLM format tests must be rewritten for compact format. Tests
asserting `"**PR**"` need updating for compact format.

### 4. `collect_branch_status()` — outer try/except safety net

**Bug**: Missing outer try/except. Base branch fallback is `"main"` instead of `"unknown"`.

**Fix**:

```python
def collect_branch_status(project_dir: Path, max_log_lines: int = 300) -> BranchStatusReport:
    try:
        # ... existing body ...
        base_branch = base_branch_result if base_branch_result else "unknown"
        # ... rest ...
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("collect_branch_status failed")
        return create_empty_report()
```

Also update `create_empty_report` to match p_coder defaults. All field differences:

- `base_branch`: `"main"` → `"unknown"`
- `current_github_label`: `""` → `"unknown"` (uses `DEFAULT_LABEL`)
- `rebase_reason`: `"unknown"` → `"Unknown"` (capital U)
- `tasks_reason`: `"unknown"` → `"Unknown"` (capital U)
- `recommendations`: `[]` → `EMPTY_RECOMMENDATIONS` (module constant)

**Tests to add**:
- Unexpected exception during collection → returns `create_empty_report()`
- `create_empty_report()` field values match p_coder defaults above

## DATA

- `_generate_recommendations` signature changes to single `report_data: Dict[str, Any]` param
- `format_for_human` output uses p_coder icon-based format with headings
- `format_for_llm` output changes to compact single-line format
- `create_empty_report()` field defaults updated per p_coder
- No changes to `BranchStatusReport` dataclass fields

**PR fields test updates**: `tests/checks/test_branch_status_pr_fields.py` assertions
need updating:
- `test_pr_found_shows_in_output`: p_coder format shows PR differently
- `test_pr_not_found_hides_pr_line`: p_coder shows "No PR found" (not absent)
- LLM format tests asserting `"**PR**"` need updating for compact format
