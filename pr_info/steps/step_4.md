# Step 4: Restore branch_status Collection Functions

**Commit**: `fix: restore branch_status collection functions`

## Context
See [summary.md](summary.md) for full issue context.
This step fixes the data-gathering functions in branch_status.py. These are the functions
that call out to CI, git, task tracker, and GitHub to collect status data.

## LLM Prompt
> Read `pr_info/steps/summary.md` and this file. Fix the collection functions in
> `src/mcp_workspace/checks/branch_status.py` as described below.
> Write tests first (TDD), then fix the source. Run all quality checks.
> Reference project `p_coder` at `src/mcp_coder/checks/branch_status.py` is the source of truth.

## WHERE

| File | Action |
|------|--------|
| `tests/checks/test_branch_status.py` | Update tests for 4 functions |
| `src/mcp_workspace/checks/branch_status.py` | Fix 4 functions + add constants + add imports |

## WHAT

**Step dependency**: This step depends on Steps 1-2 being complete (ci_log_parser functions
must have correct behavior before branch_status imports them).

**Decision #4 note**: `_collect_rebase_status` is intentionally left unchanged (keeps
`base_branch` param) per Decision #4. Do NOT port it back.

### 0. Module-level additions

Add constants and private imports from ci_log_parser:

```python
from mcp_workspace.github_operations.ci_log_parser import (
    _find_log_content,
    _strip_timestamps,
    _extract_failed_step_log,
    build_ci_error_details,
    truncate_ci_details,
)

DEFAULT_LABEL = "unknown"
EMPTY_RECOMMENDATIONS: List[str] = []
```

**Private imports lint guidance**: `_find_log_content`, `_strip_timestamps`, and
`_extract_failed_step_log` are private functions imported cross-package. To avoid pylint
warnings, add these 3 functions to ci_log_parser's `__all__` list (preferred approach,
since branch_status needs them as part of the package's internal API). This is better
than scattering pylint disable comments.

### 1. `_collect_ci_status(project_dir, branch_name, max_log_lines) -> tuple[CIStatus, Optional[str]]`

**Two bugs**:
- (a) Missing inner try/except around `build_ci_error_details` — if log fetching fails,
  the outer except catches it and returns `NOT_CONFIGURED` instead of `FAILED` with no details.
- (b) Status extraction uses separate `conclusion`/`status` vars instead of `conclusion or status`
  fallback chain.

**Fix**:

```python
# Pseudocode:
ci_manager = CIResultsManager(project_dir=project_dir)
status_result = ci_manager.get_latest_ci_status(branch_name)
run_data = status_result.get("run")
if not run_data:
    return NOT_CONFIGURED, None
ci_state = run_data.get("conclusion") or run_data.get("status", "")  # fallback chain
if ci_state == "success":
    return PASSED, None
elif ci_state == "failure":
    try:
        details = build_ci_error_details(ci_manager, status_result, max_lines=max_log_lines)
    except Exception:
        details = None  # log fetch failed, but CI IS still FAILED
    return FAILED, details
elif ci_state in ("in_progress", "queued", "pending"):
    return PENDING, None
else:
    return NOT_CONFIGURED, None
```

**Tests to update**:
- Add test: `build_ci_error_details` raising exception still returns `FAILED` (not `NOT_CONFIGURED`)
- Update test_pending: verify `conclusion or status` chain works (conclusion=None, status="in_progress")

### 2. `_collect_task_status(project_dir) -> tuple[TaskTrackerStatus, str, bool]`

**Bug**: Missing pr_info directory pre-checks (folder existence, steps files). Also
missing several behavioral differences from p_coder.

**Fix**: Port back the exact logic from p_coder. Key behavioral differences to implement:

- `total == 0` → blocking changes from `False` to `True`, reason becomes `"Task tracker is empty"`
- `TaskTrackerFileNotFoundError` with steps files present → `is_blocking=True`, message about creating task tracker
- `TaskTrackerSectionNotFoundError` → blocking is conditional on `has_steps_files`
- General `Exception` → `is_blocking=True`

Read the p_coder reference at `src/mcp_coder/checks/branch_status.py` for the exact
implementation including pre-checks for `pr_info_path.exists()` and steps dir.

**Test to add**: pr_info dir missing → returns N_A without calling get_task_counts.
**Tests to add**: `total == 0` → blocking; exception cases per above.

### 3. `_collect_github_label(issue_data) -> str`

**Bug**: Returns `""` instead of `"unknown"` as default.

**Fix**: Return `DEFAULT_LABEL` (`"unknown"`) when no issue data or no status label found.

```python
if issue_data is None:
    return DEFAULT_LABEL
# ... search for status- label ...
return DEFAULT_LABEL  # was: return ""
```

**Tests to update**: Update `TestCollectGithubLabel.test_no_status_label` and
`TestCollectGithubLabel.test_none_issue_data` in `tests/checks/test_branch_status.py`
to expect `"unknown"` instead of `""`. Note the function signature stays as
`(issue_data)` per Decision #6.

### 4. `get_failed_jobs_summary(jobs, logs) -> Dict[str, Any]`

**Bug**: Returns completely different structure than p_coder. mcp-workspace returns
`{"failed_count": N, "failed_jobs": [...]}` while p_coder returns
`{"job_name": ..., "step_name": ..., "step_number": ..., "log_excerpt": ..., "other_failed_jobs": []}`.

**Fix**: Port back the exact return structure from p_coder reference project
`src/mcp_coder/checks/branch_status.py` function `get_failed_jobs_summary`. Use
`mcp__workspace__read_reference_file` to read the p_coder implementation. The return
value is a dict with keys `job_name`, `step_name`, `step_number`, `log_excerpt`, and
`other_failed_jobs`. Per Decision #15 ("port back with full log excerpt functionality").

**Tests to rewrite**: Existing tests asserting `result["failed_count"]` and
`result["failed_jobs"]` must be rewritten to match the p_coder return structure.

## DATA

- `DEFAULT_LABEL = "unknown"` — new module constant
- `EMPTY_RECOMMENDATIONS: List[str] = []` — new module constant
- `_collect_github_label` now returns `"unknown"` instead of `""`
- `get_failed_jobs_summary` step dicts gain optional `log_excerpt` key
