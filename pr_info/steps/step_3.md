# Step 3: Character budget and compact fallback

## Context
See `pr_info/steps/summary.md` for full context. This step replaces newline-counting with a character budget and adds a compact fallback that always provides the complete file/line map when results are truncated.

## WHERE
- `src/mcp_workspace/file_tools/search.py` — `_search_content()` function
- `tests/file_tools/test_search.py` — update existing truncation test + new tests

## WHAT
1. Replace `total_lines_so_far` with `chars_used` counter. Budget = `max_result_lines * 120`.
2. Track all matches in a `files_map: Dict[str, List[int]]` for the compact fallback.
3. When `truncated=True`, include `"matched_files"` key in return dict (converted from files_map).
4. When `truncated=False`, do NOT include `"matched_files"` key.

## ALGORITHM
```python
char_budget = max_result_lines * 120
chars_used = 0
files_map: Dict[str, List[int]] = {}  # all matches, even after budget hit

for each match found:
    total_matches += 1
    files_map.setdefault(rel_path, []).append(i + 1)
    
    if truncated:
        continue
    
    context = <build context with per-line truncation from step 2>
    
    if len(details) >= max_results or chars_used + len(context) > char_budget:
        truncated = True
        continue
    
    details.append({"file": rel_path, "line": i + 1, "text": context})
    chars_used += len(context)

# Return
result = {"mode": "content_search", "details": details, "total_matches": total_matches, "truncated": truncated}
if truncated:
    result["matched_files"] = [{"file": f, "lines": lns} for f, lns in files_map.items()]
return result
```

## DATA
**Not truncated:**
```python
{"mode": "content_search", "details": [...], "total_matches": N, "truncated": False}
```

**Truncated:**
```python
{
    "mode": "content_search",
    "details": [...],  # as many as fit in budget
    "matched_files": [{"file": "foo.py", "lines": [42, 87]}, ...],  # always complete
    "total_matches": N,
    "truncated": True,
}
```

## Tests (TDD — write first)

### Update existing test
`test_search_files_max_result_lines_truncation` — update to verify char-budget semantics instead of line-counting. The test uses `max_result_lines=5` which gives `char_budget = 5 * 120 = 600`. Each match line like `"match_line_0"` is ~12 chars, so many should fit but not all 20.

```python
def test_search_files_char_budget_truncation(self, project_dir: Path) -> None:
    """Verify char budget (max_result_lines * 120) triggers truncation."""
    lines = [f"match_line_{i}" for i in range(20)]
    (project_dir / "many.txt").write_text("\n".join(lines) + "\n")

    result = search_files(
        project_dir,
        pattern=r"match_line_",
        max_results=100,
        max_result_lines=1,  # budget = 1 * 120 = 120 chars
    )

    assert result["truncated"] is True
    total_chars = sum(len(m["text"]) for m in result["details"])
    assert total_chars <= 120
    assert result["total_matches"] == 20
```

### New tests

```python
class TestSearchFilesCompactFallback:
    """Tests for compact fallback when results are truncated."""

    def test_files_key_present_when_truncated(self, project_dir: Path) -> None:
        """When truncated, 'matched_files' key contains complete file/line map."""
        lines = [f"match_{i}" for i in range(50)]
        (project_dir / "big.txt").write_text("\n".join(lines) + "\n")

        result = search_files(
            project_dir,
            pattern=r"match_",
            max_results=100,
            max_result_lines=1,  # tiny budget forces truncation
        )

        assert result["truncated"] is True
        assert "matched_files" in result
        files_entry = result["matched_files"][0]
        assert files_entry["file"].endswith("big.txt")
        # All 50 matches should be in the files map
        assert len(files_entry["lines"]) == 50

    def test_files_key_absent_when_not_truncated(self, project_dir: Path) -> None:
        """When not truncated, 'matched_files' key is not in the response."""
        (project_dir / "small.txt").write_text("hello world\n")

        result = search_files(project_dir, pattern=r"hello")

        assert result["truncated"] is False
        assert "matched_files" not in result

    def test_compact_fallback_multiple_files(self, project_dir: Path) -> None:
        """Compact fallback tracks matches across multiple files."""
        d = project_dir / "multi"
        d.mkdir()
        (d / "a.py").write_text("target line 1\ntarget line 2\n")
        (d / "b.py").write_text("target line 3\n")

        result = search_files(
            project_dir,
            pattern=r"target",
            max_results=100,
            max_result_lines=1,  # tiny budget
        )

        assert result["truncated"] is True
        assert result["total_matches"] == 3
        file_names = {e["file"] for e in result["matched_files"]}
        assert any("a.py" in f for f in file_names)
        assert any("b.py" in f for f in file_names)

    def test_empty_details_when_first_match_exceeds_budget(self, project_dir: Path) -> None:
        """When even the first match exceeds char budget, details is empty but matched_files is populated."""
        long_line = "x" * 200
        (project_dir / "huge.txt").write_text(long_line + "\n")

        result = search_files(
            project_dir,
            pattern=r"x+",
            max_results=100,
            max_result_lines=1,  # budget = 120 chars, truncated line ~236 chars
        )

        assert result["truncated"] is True
        assert result["details"] == []
        assert len(result["matched_files"]) == 1
        assert result["total_matches"] == 1

    def test_long_line_char_budget(self, project_dir: Path) -> None:
        """A single long-line match can exhaust char budget on its own."""
        # 600 char line, with max_result_lines=5 -> budget=600
        # After per-line truncation to 500 + marker, context is ~540 chars
        # Second match should not fit
        long = "x" * 600
        (project_dir / "two.txt").write_text(f"{long}\n{long}\n")

        result = search_files(
            project_dir,
            pattern=r"x+",
            max_results=100,
            max_result_lines=5,  # budget = 600
        )

        # At least one match fits, but both may not
        assert len(result["details"]) >= 1
        assert result["total_matches"] == 2
        assert result["truncated"] is True
        assert "matched_files" in result
```

## Commit
`feat: add char budget and compact fallback for large search results`

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement step 3: replace newline-counting with a character budget and add compact fallback
in _search_content() in src/mcp_workspace/file_tools/search.py.

Follow TDD: first add/update the tests from the step file in tests/file_tools/test_search.py,
verify they fail, then implement the char budget and compact fallback logic. The existing
test_search_files_max_result_lines_truncation should be replaced with
test_search_files_char_budget_truncation.

Key changes in _search_content():
- Replace total_lines_so_far with chars_used, budget = max_result_lines * 120
- Add files_map dict tracking all matches (file -> line numbers)
- Include "matched_files" key in return dict only when truncated=True
- Convert files_map to list-of-dicts format: [{"file": str, "lines": [int]}]

Run all quality checks after.
```
