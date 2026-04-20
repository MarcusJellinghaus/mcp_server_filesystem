# Step 2: Add ci_log_parser to github_operations

> See [summary.md](./summary.md) for full context. This is step 2 of 6.

## Goal

Move `ci_log_parser.py` from mcp-coder `checks/` into `mcp_workspace/github_operations/`. This module parses GitHub Actions log output — it belongs in `github_operations/` because it's specific to the GitHub Actions log format. No new packages needed (target package exists).

## LLM Prompt

```
Implement step 2 from pr_info/steps/step_2.md. Read pr_info/steps/summary.md for context.
Copy ci_log_parser.py from mcp-coder's src/mcp_coder/checks/ci_log_parser.py into
src/mcp_workspace/github_operations/ci_log_parser.py. Adjust imports only.
Copy the test file. All checks must pass.
```

## WHERE

| Action | Path |
|--------|------|
| Create | `src/mcp_workspace/github_operations/ci_log_parser.py` |
| Create | `tests/github_operations/test_ci_log_parser.py` |

## WHAT — Source module

**File**: `src/mcp_workspace/github_operations/ci_log_parser.py`

Copied 1:1 from mcp-coder. Key public functions (signatures preserved):

```python
def truncate_ci_details(
    details: str, max_lines: int = 300, head_lines: int = 10
) -> str:
    """Truncate CI details with head + tail preservation."""
```

Also contains internal helpers used by `branch_status.py` (re-exported there):

```python
def _strip_timestamps(log_content: str) -> str: ...
def _parse_groups(log_content: str) -> List[Tuple[str, List[str]]]: ...
def _extract_failed_step_log(log_content: str, step_name: str) -> str: ...
def _find_log_content(logs, job_name, step_number, step_name) -> str: ...
def _build_ci_error_details(ci_manager, status_result, max_lines) -> Optional[str]: ...
```

Note: `_build_ci_error_details` takes a `CIResultsManager` instance (TYPE_CHECKING import only).

## HOW — Import adjustments

- `from mcp_coder.utils.github_operations.ci_results_manager import CIResultsManager` (TYPE_CHECKING only) → `from mcp_workspace.github_operations.ci_results_manager import CIResultsManager`
- Any `from mcp_coder.checks.ci_log_parser` in tests → `from mcp_workspace.github_operations.ci_log_parser`

## ALGORITHM — `_build_ci_error_details` (pseudocode)

```
1. Extract failed jobs from status_result["jobs"]
2. Fetch logs for up to 3 failed run_ids via ci_manager.get_run_logs()
3. For each failed job: find log content, strip timestamps, extract failed step section
4. Build output with job headers, log content, and truncation as needed
5. Return structured multi-line string or None
```

## WHAT — Tests

**File**: `tests/github_operations/test_ci_log_parser.py`

Copied 1:1 from mcp-coder's `tests/checks/test_ci_log_parser.py`. Only adjust imports:
- `from mcp_coder.checks.ci_log_parser` → `from mcp_workspace.github_operations.ci_log_parser`

## DATA — Return structures

`truncate_ci_details` returns: `str` — truncated log content with head + tail preservation.

`_build_ci_error_details` returns: `Optional[str]` — structured CI error details with failed job summaries and log excerpts, or None if no logs available.

## Commit

```
feat: add ci_log_parser to github_operations

Move ci_log_parser.py from mcp-coder checks into
mcp_workspace.github_operations. Adjust imports only, no logic changes.

Ref: #114
```
