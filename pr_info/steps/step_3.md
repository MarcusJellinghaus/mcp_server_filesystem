# Step 3: Add PR and Search Formatters (`format_pr_view`, `format_search_results`)

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## LLM Prompt

> Implement Step 3 of issue #78 (see `pr_info/steps/summary.md`).
> Add `format_pr_view` and `format_search_results` to the existing `src/mcp_workspace/github_operations/formatters.py`. These are pure formatting functions taking plain dicts/lists and returning text. Write tests first (TDD), then implement. Run all code quality checks before committing.

## WHERE

- **Modify**: `src/mcp_workspace/github_operations/formatters.py`
- **Modify**: `tests/github_operations/test_formatters.py`

## WHAT

### New types (defined in `formatters.py` — lightweight, formatter-local)

```python
class ReviewData(TypedDict):
    user: Optional[str]
    state: str        # APPROVED, CHANGES_REQUESTED, COMMENTED
    body: str

class InlineCommentData(TypedDict):
    path: str
    line: Optional[int]
    user: Optional[str]
    body: str
```

### Functions

```python
def format_pr_view(
    pr: Dict[str, Any],
    reviews: Optional[List[ReviewData]] = None,
    conversation_comments: Optional[List[CommentData]] = None,
    inline_comments: Optional[List[InlineCommentData]] = None,
    max_lines: int = 200,
) -> str:
    """Format a single PR with full detail for LLM consumption."""

def format_search_results(
    items: List[Dict[str, Any]],
    max_results: int = 30,
) -> str:
    """Format search results as compact summary lines."""
```

## HOW

- `format_pr_view` takes a plain dict for PR data (matching `PullRequestData` shape but not importing it to avoid coupling)
- Reviews, comments, inline comments are optional (only present when `include_comments=True`)
- `format_search_results` items have `number`, `title`, `state`, `labels`, `pull_request` (to distinguish issues from PRs)
- Uses `truncate_output` from step 2

## ALGORITHM

### `format_pr_view`
```
parts = [f"# PR #{pr[number]}: {pr[title]}"]
parts.append(f"State: {pr[state]} | {pr[head_branch]} → {pr[base_branch]} | Draft: {pr[draft]} | Merged: {pr[merged]}")
parts.append(pr[body] or "(no description)")
if reviews: parts.append("## Reviews")
    for r in reviews: parts.append(f"**{r[user]}**: {r[state]}\n{r[body]}")
if conversation_comments: parts.append("## Comments ({len})")
    for c in conversation_comments: parts.append(f"**{c[user]}** ({c[created_at]}):\n{c[body]}")
if inline_comments: parts.append("## Inline Review Comments ({len})")
    for ic in inline_comments: parts.append(f"{ic[path]}:{ic[line]} ({ic[user]}): \"{ic[body]}\"")
return truncate_output("\n\n".join(parts), max_lines)
```

### `format_search_results`
```
if not items: return "No results found."
lines = []
for item in items[:max_results]:
    kind = "PR" if item.get("pull_request") else "Issue"
    labels = ", ".join(item.get("labels", []))
    lines.append(f"#{item[number]} [{kind}] [{item[state]}] {item[title]}  {labels}")
if len(items) > max_results:
    lines.append(f"\n... {len(items)} total results. Showing first {max_results}. Refine your query for more specific results.")
return "\n".join(lines)
```

## DATA

- `format_pr_view` input: PR dict + optional review/comment lists + `max_lines`
- `format_pr_view` output: multi-line formatted text
- `format_search_results` input: list of search result dicts + `max_results`
- `format_search_results` output: compact one-line-per-result text with Issue/PR indicator

## TESTS

In `tests/github_operations/test_formatters.py`:

### `format_pr_view`
1. `test_format_pr_view_basic` — title, state, branches, body rendered
2. `test_format_pr_view_with_reviews` — review verdicts rendered
3. `test_format_pr_view_with_conversation_comments` — conversation comments rendered
4. `test_format_pr_view_with_inline_comments` — compact `path:line (user): "body"` format
5. `test_format_pr_view_no_comments` — no comment sections when all None
6. `test_format_pr_view_truncation` — long output truncated with indicator
7. `test_format_pr_view_merged_draft_flags` — merged/draft status displayed

### `format_search_results`
1. `test_format_search_results_basic` — renders summary lines
2. `test_format_search_results_empty` — "No results found." message
3. `test_format_search_results_issue_vs_pr` — correct Issue/PR indicator
4. `test_format_search_results_max_results_cap` — excess results truncated with guidance

## COMMIT

```
feat(github): add PR view and search result formatters (#78)
```
