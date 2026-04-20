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

Copied 1:1 from mcp-coder. Key functions (signatures preserved):

```python
def parse_failed_log_section(log_text: str) -> list[dict[str, str]]:
    """Parse GitHub Actions log text, extract failed step sections."""

def get_failed_jobs_summary(
    ci_status: dict[str, Any],
    ci_manager: "CIResultsManager",
    max_log_lines: int = 300,
) -> str:
    """Fetch logs for failed jobs, parse them, return formatted summary."""
```

## HOW — Import adjustments

- `from mcp_coder.mcp_workspace_git` → direct imports from `mcp_workspace.github_operations` (e.g., `CIResultsManager`)
- Any `from mcp_coder.checks.ci_log_parser` in tests → `from mcp_workspace.github_operations.ci_log_parser`

## ALGORITHM — `get_failed_jobs_summary` (pseudocode)

```
1. Extract failed jobs from ci_status dict
2. For each failed job, fetch log via ci_manager.get_job_log(job_id)
3. Parse log with parse_failed_log_section()
4. Truncate to max_log_lines
5. Format and concatenate all failed job summaries
6. Return formatted string
```

## WHAT — Tests

**File**: `tests/github_operations/test_ci_log_parser.py`

Copied 1:1 from mcp-coder's `tests/checks/test_ci_log_parser.py`. Only adjust imports:
- `from mcp_coder.checks.ci_log_parser` → `from mcp_workspace.github_operations.ci_log_parser`

## DATA — Return structures

`parse_failed_log_section` returns:
```python
[
    {"step_name": "Run tests", "log_content": "FAILED test_foo.py ..."},
]
```

`get_failed_jobs_summary` returns a formatted multi-line string.

## Commit

```
feat: add ci_log_parser to github_operations

Move ci_log_parser.py from mcp-coder checks into
mcp_workspace.github_operations. Adjust imports only, no logic changes.

Ref: #114
```
