# Step 2: Create `formatters.py` — Issue Formatters (`format_issue_view`, `format_issue_list`)

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## LLM Prompt

> Implement Step 2 of issue #78 (see `pr_info/steps/summary.md`).
> Create `src/mcp_workspace/github_operations/formatters.py` with two pure formatting functions: `format_issue_view` and `format_issue_list`. These take data dicts (not PyGithub objects) and return formatted text strings. Also create the test file. Write tests first (TDD), then implement. Run all code quality checks before committing.

## WHERE

- **Create**: `src/mcp_workspace/github_operations/formatters.py`
- **Create**: `tests/github_operations/test_formatters.py`

## WHAT

### Functions

```python
def truncate_output(text: str, max_lines: int) -> str:
    """Apply max_lines truncation with indicator."""

def format_issue_view(
    issue: IssueData,
    comments: List[CommentData],
    max_lines: int = 200,
) -> str:
    """Format a single issue with full detail for LLM consumption."""

def format_issue_list(
    issues: List[IssueData],
    max_results: int = 30,
) -> str:
    """Format issue list as compact summary lines (no body)."""
```

## HOW

- Import `IssueData`, `CommentData` from `github_operations.issues.types` (type references only)
- Pure functions — no API calls, no manager dependencies
- `truncate_output` is a shared helper used by all view formatters

## ALGORITHM

### `truncate_output`
```
lines = text.splitlines()
if len(lines) <= max_lines: return text
total = len(lines)
return "\n".join(lines[:max_lines]) + f"\n\n... truncated, {total} lines total"
```

### `format_issue_view`
```
parts = [f"# #{issue[number]}: {issue[title]}"]
parts.append(f"State: {issue[state]} | Labels: {labels} | Assignees: {assignees}")
parts.append(issue[body] or "(no description)")
if comments: parts.append("## Comments ({len})")
    for c in comments: parts.append(f"**{c[user]}** ({c[created_at]}):\n{c[body]}")
return truncate_output("\n\n".join(parts), max_lines)
```

### `format_issue_list`
```
if not issues: return "No issues found."
lines = []
for issue in issues[:max_results]:
    labels_str = ", ".join(issue[labels]) or ""
    lines.append(f"#{issue[number]} [{issue[state]}] {issue[title]}  {labels_str}")
if len(issues) > max_results:
    lines.append(f"\n... {len(issues)} total results. Showing first {max_results}. Refine your query for more specific results.")
return "\n".join(lines)
```

## DATA

- `format_issue_view` input: `IssueData` dict + `List[CommentData]` + `max_lines`
- `format_issue_view` output: multi-line formatted text string
- `format_issue_list` input: `List[IssueData]` + `max_results`
- `format_issue_list` output: compact one-line-per-issue text

## TESTS

In `tests/github_operations/test_formatters.py`:

### `truncate_output`
1. `test_truncate_output_no_truncation` — text within limit returned as-is
2. `test_truncate_output_truncation` — text exceeding limit truncated with indicator
3. `test_truncate_output_exact_limit` — text at exact limit not truncated

### `format_issue_view`
1. `test_format_issue_view_basic` — title, state, labels, body rendered
2. `test_format_issue_view_with_comments` — comments section rendered
3. `test_format_issue_view_no_comments` — no comments section when empty list
4. `test_format_issue_view_truncation` — long output truncated with indicator
5. `test_format_issue_view_empty_body` — "(no description)" placeholder

### `format_issue_list`
1. `test_format_issue_list_basic` — renders summary lines
2. `test_format_issue_list_empty` — "No issues found." message
3. `test_format_issue_list_max_results_cap` — excess issues truncated with guidance
4. `test_format_issue_list_labels` — labels rendered in summary line

## COMMIT

```
feat(github): add issue formatters for view and list tools (#78)
```
