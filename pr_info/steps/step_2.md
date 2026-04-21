# Step 2: Per-line truncation (500 char cap)

## Context
See `pr_info/steps/summary.md` for full context. This step adds per-line truncation to prevent single long lines from dominating the output.

## WHERE
- `src/mcp_workspace/file_tools/search.py` — `_search_content()`, between context block assembly (line 47-49) and the append (line 59)
- `tests/file_tools/test_search.py` — new test class or tests for long-line truncation

## WHAT
Truncate every line in the context block to 500 chars. When a line is truncated, append ` ... [truncated, line has {n} chars]`.

### Constant
```python
_MAX_LINE_CHARS = 500
```

## HOW
In `_search_content()`, after assembling the context lines (lines 47-49), process each line individually before joining:

## ALGORITHM
```python
_MAX_LINE_CHARS = 500

# Replace the current context assembly (lines 47-49):
#   context = "".join(file_lines[start:end]).rstrip("\n")
# With:
raw_lines = file_lines[start:end]
capped = []
for raw in raw_lines:
    stripped = raw.rstrip("\n")
    if len(stripped) > _MAX_LINE_CHARS:
        stripped = stripped[:_MAX_LINE_CHARS] + f" ... [truncated, line has {len(stripped)} chars]"
    capped.append(stripped)
context = "\n".join(capped)
```

## DATA
Each detail entry `{"file": str, "line": int, "text": str}` — the `"text"` field now has each line capped at 500 chars (plus truncation marker if applicable).

## Tests (TDD — write first)
Add to `tests/file_tools/test_search.py`:

```python
class TestSearchFilesLineTruncation:
    """Tests for per-line truncation of long lines."""

    def test_long_line_truncated_at_500_chars(self, project_dir: Path) -> None:
        """A line exceeding 500 chars is truncated with marker."""
        long_line = "x" * 1000
        (project_dir / "long.txt").write_text(long_line + "\n")

        result = search_files(project_dir, pattern=r"x+")

        detail = result["details"][0]
        assert len(detail["text"]) < 1000
        assert "... [truncated, line has 1000 chars]" in detail["text"]
        assert detail["text"].startswith("x" * 500)

    def test_short_line_not_truncated(self, project_dir: Path) -> None:
        """A line under 500 chars is returned as-is."""
        line = "y" * 499
        (project_dir / "short.txt").write_text(line + "\n")

        result = search_files(project_dir, pattern=r"y+")

        assert result["details"][0]["text"] == line
        assert "truncated" not in result["details"][0]["text"]

    def test_context_lines_also_truncated(self, project_dir: Path) -> None:
        """Context lines (not just match line) are truncated too."""
        long_ctx = "a" * 800
        (project_dir / "ctx.txt").write_text(f"{long_ctx}\nMATCH\nshort\n")

        result = search_files(project_dir, pattern=r"MATCH", context_lines=1)

        text = result["details"][0]["text"]
        lines = text.split("\n")
        # First line (context) should be truncated
        assert "... [truncated, line has 800 chars]" in lines[0]
        # Match line should be intact
        assert lines[1] == "MATCH"
```

## Commit
`feat: add per-line truncation to search content results`

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement step 2: add per-line truncation (500 char cap) to _search_content() in
src/mcp_workspace/file_tools/search.py.

Follow TDD: first add the tests from the step file to tests/file_tools/test_search.py,
verify they fail, then implement the _MAX_LINE_CHARS constant and the truncation logic
in _search_content(). Run all quality checks after.
```
