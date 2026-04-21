# Issue #128: Port Back branch_status and ci_log_parser from p_coder

## Problem

`check_branch_status` reports CI as FAILED even when GitHub Actions shows green.
CI failure details are missing from the output. This is a regression — during migration
from p_coder to mcp-workspace (PRs #108 and #121), `branch_status.py` and `ci_log_parser.py`
were rewritten rather than faithfully ported.

## Fix Strategy

Accurate port-back of original p_coder logic into mcp-workspace module structure.
**Guiding principle: in case of doubt, port back.** Only deviate where an explicit Decision
marks something as a deliberate mcp-workspace enrichment.

## Architectural / Design Changes

### No structural changes
- No new modules or packages created
- No changes to the layered architecture (checks → github_operations → git_operations)
- No new dependencies

### Behavioral restorations
- **ci_log_parser.py**: Internal functions restored to match GitHub Actions log format
  (`_{job_name}.txt` suffix matching, `##[group]` startswith, unanchored timestamps).
  `build_ci_error_details` changes from "returns None when no logs" to "always produces
  a report with job names/URLs even without log content."
- **branch_status.py**: Error handling hardened (inner try/except in `_collect_ci_status`,
  outer try/except in `collect_branch_status`). Recommendations become richer (blocking
  logic, "Ready to merge"/"Continue" messages). Output formats restored (icons in human,
  compact in LLM). Default label becomes `"unknown"` instead of `""`.
- **ci_results_manager.py**: `github_token` passthrough on `__init__` (base class already
  supports it, subclass just wasn't exposing it).

### Design principle preserved
- All 5 mcp-workspace enrichments retained (Decisions #2, #4, #5, #6, #12)
- Import paths use mcp-workspace layout, not p_coder layout

## Files Modified

| File | Change Type |
|------|-------------|
| `src/mcp_workspace/github_operations/ci_log_parser.py` | Fix ~6 functions |
| `src/mcp_workspace/github_operations/ci_results_manager.py` | Add 1 param |
| `src/mcp_workspace/checks/branch_status.py` | Fix ~8 functions + constants + formats |
| `tests/github_operations/test_ci_log_parser.py` | Update tests for fixed behavior |
| `tests/github_operations/test_ci_results_manager_foundation.py` | Add 1 test |
| `tests/checks/test_branch_status.py` | Update tests for fixed behavior |
| `tests/checks/test_branch_status_pr_fields.py` | Update format assertions |

## Implementation Steps

| Step | Scope | Commit message |
|------|-------|----------------|
| 1 | ci_log_parser.py internals: `_strip_timestamps`, `_parse_groups`, `_extract_failed_step_log` | fix: restore ci_log_parser internal parsing functions |
| 2 | ci_log_parser.py: `_find_log_content` + `build_ci_error_details` + `truncate_ci_details` | fix: restore ci_log_parser report building logic |
| 3 | ci_results_manager.py: add `github_token` param | fix: add github_token passthrough to CIResultsManager |
| 4 | branch_status.py: collection functions (`_collect_ci_status`, `_collect_task_status`, `_collect_github_label`, `get_failed_jobs_summary`) | fix: restore branch_status collection functions |
| 5 | branch_status.py: `_generate_recommendations` + `format_for_human` + `format_for_llm` + constants + outer safety | fix: restore branch_status recommendations and output formats |

## Key Decisions (from issue)

| # | Decision | Rationale |
|---|----------|-----------|
| 2 | Keep `_collect_pr_info()` | mcp-workspace addition |
| 4 | Keep `base_branch` param on `_collect_rebase_status()` | mcp-workspace enrichment |
| 5 | Keep enriched `detect_base_branch()` call | mcp-workspace passes extra managers |
| 6 | Keep `_collect_github_label(issue_data)` signature, restore `"unknown"` default | Simpler signature, correct default |
| 7 | Port back inner try/except + `conclusion or status` chain | Critical bug fix |
| 12 | Skip `from __future__ import annotations` | Python 3.11+ |
