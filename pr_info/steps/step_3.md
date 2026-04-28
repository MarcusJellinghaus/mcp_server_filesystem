# Step 3 — Add `_format_pr_feedback()` pure formatter

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`).
> Implement Step 3 only. Follow TDD: write the tests in `tests/checks/test_branch_status_pr_feedback.py` first, then add the helper in `branch_status.py`. Run pylint + pytest + mypy and confirm all green. Produce exactly one commit.

## Goal

Add a pure formatting helper `_format_pr_feedback(feedback)` that turns a `PRFeedback` dict into the rendered "PR Reviews:" block (or the empty-state affirmation). This is a stateless pure function — easy to test in isolation. Wiring into the report happens in Step 4.

## WHERE

- `src/mcp_workspace/checks/branch_status.py` — add module-level constants `_MAX_FEEDBACK_ITEMS = 20`, `_MAX_LINES_PER_COMMENT = 10`, and the helper `_format_pr_feedback`.
- `tests/checks/test_branch_status_pr_feedback.py` — new test file.

## WHAT

```python
from mcp_workspace.github_operations.pr_manager import PRFeedback

_MAX_FEEDBACK_ITEMS = 20
_MAX_LINES_PER_COMMENT = 10


def _format_pr_feedback(feedback: PRFeedback) -> str:
    """Render the PRFeedback block as a string.

    Empty-state output:
        "Reviews: clean (0 unresolved threads, 0 alerts)"

    Populated output (matches issue example):
        "PR Reviews:\\n[unresolved thread] ...\\n[comment] ...\\n[changes_requested] ...\\n[alert] ...\\n12 resolved threads"
    """
```

## HOW

- Pure function — no I/O, no exceptions raised, takes a `PRFeedback` and returns `str`.
- Truncate body lines per item to `_MAX_LINES_PER_COMMENT` with `... (truncated)` marker.
- Total items rendered (sum of unresolved_threads + comments + changes_requested + alerts) capped at `_MAX_FEEDBACK_ITEMS` with `... and N more` marker.
- For each entry in `feedback["unavailable"]`, render one line: `[unavailable] {section}: API error`.
- Resolved threads rendered as a single trailing line `"{n} resolved threads"` only when `n > 0`.

## ALGORITHM

```text
1. blocking = unresolved_threads or changes_requested or alerts
2. nothing_to_show = not blocking and not conversation_comments and not unavailable
3. if nothing_to_show:
       return "Reviews: clean (0 unresolved threads, 0 alerts)"
4. lines = ["PR Reviews:"]
5. emit each unresolved_thread → "[unresolved thread] {path}:{line} ({author}):\n  {diff_hunk indented}\n  Comment: {body truncated}"
6. emit each conversation_comment → "[comment] {author}:\n  {body truncated}"
7. emit each changes_requested → "[changes_requested] {author}: {body truncated}"
8. emit each alert → "[alert] {rule}: {message} @ {path}:{line}"
9. cap total rendered items at _MAX_FEEDBACK_ITEMS, append "... and {N} more" if exceeded
10. emit one line per entry in feedback["unavailable"]: "[unavailable] {section}: API error"
11. if resolved_thread_count > 0: append "{n} resolved threads"
12. return "\n".join(lines)
```

## DATA

- Input: `PRFeedback` (from Step 2).
- Output: `str` — multi-line block, no trailing newline.

## Tests (write these first — `tests/checks/test_branch_status_pr_feedback.py`)

1. **Empty feedback** → returns the affirmation line `"Reviews: clean (0 unresolved threads, 0 alerts)"`.
2. **Only unresolved threads** → header `"PR Reviews:"`, contains `[unresolved thread]`, includes `path:line`, includes diff hunk, includes comment body.
3. **Only conversation comments** → contains `[comment]` lines with author + body.
4. **Only `changes_requested`** → contains `[changes_requested]` lines with author + body.
5. **Only alerts** → contains `[alert]` lines with rule + path:line.
6. **Resolved threads count** → trailing `"12 resolved threads"` when `resolved_thread_count == 12`; absent when `0`.
7. **Body truncation** → comment body of 20 lines is truncated to 10 + `"... (truncated)"`.
8. **Item cap** → 30 mixed items render only 20 + `"... and 10 more"`.
9. **Unavailable section** → `unavailable=["threads"]` produces `"[unavailable] threads: API error"`.
10. **Mixed full example** matching the issue spec output.

## Exit criteria

- pylint passes
- mypy passes (`PRFeedback` import resolves; pure-function signature is fully typed)
- pytest passes (new test file green; existing tests untouched)
- One commit on the branch
