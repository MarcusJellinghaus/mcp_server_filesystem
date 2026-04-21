# Step 2: Restore ci_log_parser Report Building Logic

**Commit**: `fix: restore ci_log_parser report building logic`

## Context
See [summary.md](summary.md) for full issue context.
This step fixes `_find_log_content`, `build_ci_error_details`, and `truncate_ci_details`.
These are the functions that construct the CI error report consumed by branch_status.

## LLM Prompt
> Read `pr_info/steps/summary.md` and this file. Fix `_find_log_content`,
> `build_ci_error_details`, and `truncate_ci_details` in
> `src/mcp_workspace/github_operations/ci_log_parser.py` as described below.
> Write tests first (TDD), then fix the source. Run all quality checks.
> Reference project `p_coder` at `src/mcp_coder/checks/ci_log_parser.py` is the source of truth.

## WHERE

| File | Action |
|------|--------|
| `tests/github_operations/test_ci_log_parser.py` | Update/add tests for 3 functions |
| `src/mcp_workspace/github_operations/ci_log_parser.py` | Fix 3 functions |

## WHAT

### 1. `_find_log_content(logs, job_name, step_number, step_name) -> str`

**Bug**: Lost GitHub's `_{job_name}.txt` suffix matching (the primary log lookup strategy
in p_coder). Current code uses loose substring matching which can match wrong files.

**Fix**: Add `_{job_name}.txt` suffix matching as first strategy, keep existing matching
as fallback tiers.

```python
# Pseudocode:
# Tier 1: GitHub's native format — filename ends with "_{job_name}.txt"
for filename, content in logs.items():
    if filename.endswith(f"_{job_name}.txt"):
        # then match step within this content
        return _extract_failed_step_log(content, step_name)

# Tier 2: existing job_name + step_number match (keep current)
# Tier 3: existing job_name + step_name match (keep current)
# Tier 4: existing job_name only match (keep current)
# Tier 5: return ""
```

**Test to add**: Log dict with `"some_path/0_Job Name.txt"` key — verify `_{job_name}.txt`
suffix match works.

### 2. `build_ci_error_details(ci_manager, status_result, max_lines) -> str`

**Critical behavioral change**: Must NEVER return `None`. p_coder always produces a report
even without log content (shows job names, step names, GitHub URLs).

**Fix**: Port back the exact logic from p_coder reference project
`src/mcp_coder/checks/ci_log_parser.py` function `_build_ci_error_details`. Keep the
public name `build_ci_error_details` per Decision #3. The function must include: run URL
in output, per-job line budget tracking, job URL links, summary header,
`jobs_fetch_warning` handling, and "truncated jobs" section. Never return None — return
`""` for no failed jobs.

Use `mcp__workspace__read_reference_file` with the p_coder project to read the exact
implementation (~100 lines). Do NOT rely on the pseudocode skeleton that was previously
here — it was far too vague for this complex function.

**Return type change**: `Optional[str]` → `str` (never None).

**Tests to update**:
- `test_returns_none_for_no_jobs` → returns `""` not `None`
- `test_returns_none_for_no_failed_jobs` → returns `""` not `None`
- `test_returns_none_when_no_logs_available` → returns string with job names/URLs (not None)
- `test_handles_log_fetch_failure` → returns string with job info (not None)
- Add test: run URL is included in output
- Add test: per-job line budget — verify truncation message for excess jobs

### 3. `truncate_ci_details(details, max_lines, head_lines) -> str`

**Bug**: Truncation marker format differs from p_coder.

**Fix**: Match p_coder's marker format exactly. P_coder uses square brackets and
different word order:

```python
# BEFORE (mcp-workspace):
f"\n... ({skipped} lines truncated) ...\n"
# AFTER (match p_coder):
f"[... truncated {truncated_count} lines ...]"
```

Note the variable name change: `skipped` → `truncated_count` to match p_coder.

Also add p_coder's early guard: `if not details: return ""`.

**Test to update**: `test_truncation_marker_shows_count` — verify square bracket format
and no extra blank lines around marker.

## DATA

- `build_ci_error_details` return type: `Optional[str]` → `str`
- `__all__` export list: unchanged
- `truncate_ci_details`: same signature, format change (square brackets)

**Return type safety note**: Changing `build_ci_error_details` return type from
`Optional[str]` to `str` is safe for existing callers — `str` is a subtype of
`Optional[str]`, so mypy won't break in Steps 3-4 before the caller is updated in
later steps.
