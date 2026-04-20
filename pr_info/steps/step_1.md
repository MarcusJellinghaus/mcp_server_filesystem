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

Copied 1:1 from mcp-coder. Key public classes, functions, and their signatures:

```python
# --- Data classes ---
@dataclass
class TaskInfo:
    """Simple data model for task information."""
    name: str
    is_complete: bool
    line_number: int
    indentation_level: int

class TaskTrackerStatus(str, Enum):
    """Status of the task tracker: COMPLETE, INCOMPLETE, N_A, ERROR."""

# --- Exception classes ---
class TaskTrackerError(Exception): ...
class TaskTrackerFileNotFoundError(TaskTrackerError): ...
class TaskTrackerSectionNotFoundError(TaskTrackerError): ...

# --- Public functions ---
def get_incomplete_tasks(
    folder_path: str = "pr_info", exclude_meta_tasks: bool = False
) -> list[str]:
    """Get list of incomplete task names from Implementation Steps section."""

def has_incomplete_work(folder_path: str = "pr_info") -> bool:
    """Check if there is any incomplete work in the task tracker."""

def get_task_counts(folder_path: str = "pr_info") -> tuple[int, int]:
    """Get total and completed task counts. Returns (total, completed)."""

def get_step_progress(
    folder_path: str = "pr_info",
) -> dict[str, dict[str, int | list[str]]]:
    """Get detailed progress info for each step."""

def validate_task_tracker(folder_path: str = "pr_info") -> None:
    """Validate TASK_TRACKER.md has required structure."""

def is_task_done(task_name: str, folder_path: str = "pr_info") -> bool:
    """Check if specific task is marked as complete."""
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

`get_incomplete_tasks` returns: `list[str]` — names of incomplete tasks.

`get_task_counts` returns: `tuple[int, int]` — `(total_tasks, completed_tasks)`.

`get_step_progress` returns:
```python
{
    "Step 1: Create Package Structure": {
        "total": 5,
        "completed": 3,
        "incomplete": 2,
        "incomplete_tasks": ["Task A", "Task B"]
    },
}
```

`is_task_done` returns: `bool` — True if task is complete.

Also exports: `TASK_TRACKER_TEMPLATE` string constant for creating new tracker files.

## Commit

```
feat: add task_tracker module to workflows

Move task_tracker.py from mcp-coder workflow_utils into
mcp_workspace.workflows. Adjust imports only, no logic changes.

Ref: #114
```
