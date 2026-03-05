---
workflow-stage: utility
suggested-next: implementation_review
---

# Implementation Finalise

Complete any remaining unchecked tasks in the task tracker before transitioning to code review.

## Process

### 1. Read Task Tracker

Read `pr_info/TASK_TRACKER.md` and identify all unchecked tasks (`- [ ]`).

If all tasks are already checked (`- [x]`), report that no finalisation is needed and exit.

### 2. Process Each Unchecked Task

For each unchecked task:

#### Commit Message Tasks

If the task contains "commit message" (case-insensitive):

- if the tasks before are already done, ignore this task by marking it as done `[x]`

#### Other Tasks

- Check `pr_info/steps/` for related step files that provide context
- If step files don't exist, analyse based on task name and codebase
- Verify if the task is already complete
- If not complete: implement the required work
- If complete or successfully implemented: mark as `[x]`
- If unable to complete: DO NOT mark as done - explain the issue

### 3. Quality Checks (If Code Changed)

If any code changes were made during this process:

- Run pylint checks using the MCP server (fix all errors)
- Run pytest checks using the MCP server (fix all failures)
- Run mypy checks using the MCP server (fix all type errors)

## Output

Report:

1. Which tasks were processed
2. Which tasks were marked complete
3. Any issues encountered
4. Summarize the changes in a commit message and report it
