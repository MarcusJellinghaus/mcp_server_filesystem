# Step 2: Output Filtering Module

> **Context**: See `pr_info/steps/summary.md` for full architecture overview.

## LLM Prompt

```
Implement step 2 of issue #77 (read-only git operations).
Read pr_info/steps/summary.md for context, then read this step file.
Create the output filtering module with structure-aware diff/log filtering and truncation,
plus comprehensive unit tests using synthetic string inputs. Follow TDD.
Run all code quality checks after implementation. Produce one commit.
```

## WHERE

- **New**: `src/mcp_workspace/git_operations/output_filtering.py`
- **New**: `tests/git_operations/test_output_filtering.py`

## WHAT

### `output_filtering.py`

```python
import re
from .compact_diffs import parse_diff, FileDiff, Hunk

def filter_diff_output(text: str, search: str, context: int = 3) -> str:
    """Structure-aware diff filtering. Returns matching hunks with file/hunk headers preserved."""

def filter_log_output(text: str, search: str) -> str:
    """Structure-aware log filtering. Returns entire commit entries that match."""

def truncate_output(text: str, max_lines: int) -> str:
    """Truncate text to max_lines. Appends '[truncated — N more lines]' if truncated."""
```

## HOW

- Imports `parse_diff`, `FileDiff`, `Hunk` from `compact_diffs.py` (same package, no layer violation)
- All functions are pure: string in → string out (easy to test with synthetic data)

## ALGORITHM — `filter_diff_output`

```
1. Parse diff text using parse_diff() → list[FileDiff]
2. Compile search as regex (re.IGNORECASE)
3. For each FileDiff, for each Hunk:
     - Check if any line in hunk.lines matches the regex
     - If match: collect lines with context (±context lines around each match)
     - Rebuild hunk with hunk.header + collected lines (preserving +/-/space prefixes)
4. For each FileDiff with any matching hunks: emit file headers + matching hunks
5. If no matches: return "No matches for search pattern '{search}'"
```

## ALGORITHM — `filter_log_output`

```
1. Split text into commit entries at lines matching r"^commit [0-9a-f]{7,}"
2. Compile search as regex (re.IGNORECASE)
3. For each entry: if regex matches anywhere in the entry text, keep entire entry
4. Join kept entries
5. If no matches: return "No matches for search pattern '{search}'"
```

## ALGORITHM — `truncate_output`

```
1. Split text into lines
2. If len(lines) <= max_lines: return text unchanged
3. Take first max_lines lines
4. Append "[truncated — {remaining} more lines]"
5. Return joined result
```

## DATA

### Return Values

All functions return `str`:
- `filter_diff_output` → valid diff fragment or empty-result message
- `filter_log_output` → complete commit entries or empty-result message
- `truncate_output` → text within line budget, with truncation notice if needed

## TEST CASES (`test_output_filtering.py`)

```python
class TestFilterDiffOutput:
    def test_matching_hunk_includes_file_and_hunk_headers(): ...
    def test_non_matching_hunk_excluded(): ...
    def test_context_lines_around_match(): ...
    def test_context_zero_shows_only_matching_lines(): ...
    def test_multiple_files_only_matching_files_included(): ...
    def test_no_matches_returns_descriptive_message(): ...
    def test_search_is_case_insensitive(): ...
    def test_regex_pattern_in_search(): ...    # e.g. "foo|bar"

class TestFilterLogOutput:
    def test_matching_commit_includes_entire_entry(): ...
    def test_non_matching_commit_excluded(): ...
    def test_multi_line_commit_message_matched(): ...
    def test_no_matches_returns_descriptive_message(): ...
    def test_search_is_case_insensitive(): ...

class TestTruncateOutput:
    def test_within_limit_unchanged(): ...
    def test_over_limit_truncated_with_notice(): ...
    def test_exact_limit_unchanged(): ...
    def test_notice_shows_remaining_count(): ...
    def test_empty_string(): ...
```

### Synthetic Test Data Examples

**Diff input** (for filter tests):
```
diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1,5 +1,5 @@
 context line
-old_value = 42
+new_value = 99
 another context
 more context
diff --git a/bar.py b/bar.py
--- a/bar.py
+++ b/bar.py
@@ -10,3 +10,3 @@
 unrelated context
-unrelated_old
+unrelated_new
```

**Log input** (for filter tests):
```
commit abc1234567890
Author: Test User <test@example.com>
Date:   Mon Jan 1 00:00:00 2024

    Fix critical bug in parser

commit def4567890123
Author: Test User <test@example.com>
Date:   Tue Jan 2 00:00:00 2024

    Add new feature for export
```
