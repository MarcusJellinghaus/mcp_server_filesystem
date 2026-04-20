# Step 1: Add task_tracker module to workflows

> See [summary.md](./summary.md) for full context. This is step 1 of 6.

## Goal

Move `task_tracker.py` from mcp-coder `workflow_utils/` into `mcp_workspace/workflows/`. This is a pure markdown parser with no external dependencies — the simplest module to move first. It's also a dependency of `branch_status.py` (step 5).

## LLM Prompt

```
Implement step 1 from pr_info/steps/step_1.md. Read pr_info/steps/summary.md for context.
Copy task_tracker.py from mcp-coder's src/mcp_coder/workflow_utils/task_tracker.py into
src/mcp_workspace/workflows/task_tracker.py. Adjust imports only (mcp_coder → mcp_workspace).
Copy the test file and 5 test data fixtures. All checks must pass.
```

## WHERE

| Action | Path |
|--------|------|
| Create | `src/mcp_workspace/workflows/__init__.py` |
| Create | `src/mcp_workspace/workflows/task_tracker.py` |
| Create | `tests/workflows/__init__.py` |
| Create | `tests/workflows/test_task_tracker.py` |
| Create | `tests/workflows/test_data/*.md` (5 fixture files) |

## WHAT — Source module

**File**: `src/mcp_workspace/workflows/task_tracker.py`

Copied 1:1 from mcp-coder. Key functions (signatures preserved):

```python
def parse_task_tracker(content: str) -> list[dict[str, Any]]:
    """Parse TASK_TRACKER.md content into list of task dicts."""

def get_completion_stats(tasks: list[dict[str, Any]]) -> dict[str, int]:
    """Return {total, completed, remaining} counts."""

def format_completion_summary(stats: dict[str, int]) -> str:
    """Return human-readable completion summary string."""
```

## WHAT — Package init

**File**: `src/mcp_workspace/workflows/__init__.py`

```python
"""Workflows package — task tracking and workflow utilities."""
```

## HOW — Import adjustments

Only change: any `from mcp_coder.workflow_utils` imports become `from mcp_workspace.workflows`. No logic changes.

## WHAT — Tests

**File**: `tests/workflows/test_task_tracker.py`

Copied 1:1 from mcp-coder's `tests/workflow_utils/test_task_tracker.py`. Only adjust imports:
- `from mcp_coder.workflow_utils.task_tracker` → `from mcp_workspace.workflows.task_tracker`

**Fixtures**: Copy all 5 `.md` files from mcp-coder's `tests/workflow_utils/test_data/` to `tests/workflows/test_data/`.

## DATA — Return structures

`parse_task_tracker` returns:
```python
[
    {"text": "Task description", "completed": True, "detail_file": "steps/step_1.md"},
    {"text": "Another task", "completed": False, "detail_file": None},
]
```

`get_completion_stats` returns:
```python
{"total": 5, "completed": 3, "remaining": 2}
```

## Commit

```
feat: add task_tracker module to workflows

Move task_tracker.py from mcp-coder workflow_utils into
mcp_workspace.workflows. Adjust imports only, no logic changes.

Ref: #114
```
