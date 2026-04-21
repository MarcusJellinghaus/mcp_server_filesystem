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

### 1. `_generate_recommendations(ci_status, rebase_needed, tasks_status, tasks_reason, tasks_is_blocking, ci_details) -> List[str]`

**Bug**: Lost `tasks_is_blocking` and `ci_details` parameters. Lost "Ready to merge" /
"Continue with current work" recommendations. Lost gating of rebase recommendation on task status.

**Fix**: Restore full signature and logic.

```python
def _generate_recommendations(
    ci_status: CIStatus,
    rebase_needed: bool,
    tasks_status: TaskTrackerStatus,
    tasks_reason: str,
    tasks_is_blocking: bool = False,
    ci_details: Optional[str] = None,
) -> List[str]:
    recs: List[str] = []
    if ci_status == CIStatus.FAILED:
        recs.append("Fix CI failures before merging")
    if ci_status == CIStatus.PENDING:
        recs.append("Wait for CI to complete")
    if rebase_needed and not tasks_is_blocking:
        recs.append("Rebase onto base branch")
    if tasks_status == TaskTrackerStatus.INCOMPLETE:
        recs.append(f"Complete remaining tasks ({tasks_reason})")
    if tasks_status == TaskTrackerStatus.ERROR:
        recs.append("Fix task tracker errors")
    # Positive recommendations
    if not recs:
        if tasks_status == TaskTrackerStatus.COMPLETE:
            recs.append("Ready to merge")
        else:
            recs.append("Continue with current work")
    return recs
```

**Update caller** in `collect_branch_status` to pass the two new args:

```python
recommendations = _generate_recommendations(
    ci_status, rebase_needed, tasks_status, tasks_reason,
    tasks_is_blocking=tasks_is_blocking,
    ci_details=ci_details,
)
```

**Tests to update**:
- `test_all_good` → now expects `["Ready to merge"]` (not `[]`)
- Add test: all good with N_A tasks → expects `["Continue with current work"]`
- Add test: rebase needed but tasks blocking → rebase NOT recommended
- Update `test_multiple_issues` for new param count

### 2. `format_for_human()` — restore icon-based output

**Fix**: Use icons for status lines, matching p_coder format.

```python
def format_for_human(self) -> str:
    lines: List[str] = []
    lines.append(f"🌿 Branch: {self.branch_name}")
    lines.append(f"🎯 Base: {self.base_branch}")
    ci_icon = {"PASSED": "✅", "FAILED": "❌", "PENDING": "⏳"}.get(self.ci_status.value, "⚪")
    lines.append(f"{ci_icon} CI: {self.ci_status.value}")
    if self.ci_details:
        lines.append(f"   CI Details:\n{self.ci_details}")
    rebase_icon = "⚠️" if self.rebase_needed else "✅"
    lines.append(f"{rebase_icon} Rebase: {'NEEDED' if self.rebase_needed else 'OK'} — {self.rebase_reason}")
    task_icon = {"COMPLETE": "✅", "INCOMPLETE": "⚠️", "ERROR": "❌"}.get(self.tasks_status.value, "⚪")
    lines.append(f"{task_icon} Tasks: {self.tasks_status.value} — {self.tasks_reason}")
    lines.append(f"🏷️ Label: {self.current_github_label}")
    if self.pr_found:
        lines.append(f"🔗 PR: #{self.pr_number} ({self.pr_url})")
    if self.recommendations:
        lines.append("\n📋 Recommendations:")
        for rec in self.recommendations:
            lines.append(f"  • {rec}")
    return "\n".join(lines)
```

**Tests to update**: Assertions in `test_format_for_human` and `test_branch_status_pr_fields.py`
to check for icon characters and new format.

### 3. `format_for_llm()` — restore compact format

**Fix**: Keep the existing markdown structure but ensure CI details section comes right
after CI status line (not at the bottom), and use the truncation function.

The current format is already close to p_coder's. Main change: move CI details to appear
right after CI status rather than at the end. Keep using `truncate_ci_details`.

**Tests to update**: Verify CI details position in output.

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

Also update `create_empty_report` to use `base_branch="unknown"`.

**Tests to add**:
- Unexpected exception during collection → returns `create_empty_report()`
- `create_empty_report()` has `base_branch="unknown"`

## DATA

- `_generate_recommendations` signature gains 2 optional params: `tasks_is_blocking`, `ci_details`
- `format_for_human` output uses icon characters (🌿, ✅, ❌, etc.)
- `create_empty_report().base_branch` changes from `"main"` to `"unknown"`
- No changes to `BranchStatusReport` dataclass fields
