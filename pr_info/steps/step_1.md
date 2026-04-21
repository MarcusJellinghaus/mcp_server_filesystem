# Step 1: Restore ci_log_parser Internal Parsing Functions

**Commit**: `fix: restore ci_log_parser internal parsing functions`

## Context
See [summary.md](summary.md) for full issue context.
This step fixes the three internal helper functions in ci_log_parser.py that parse
GitHub Actions log output. These are dependencies for step 2.

## LLM Prompt
> Read `pr_info/steps/summary.md` and this file. Fix the three internal parsing functions
> in `src/mcp_workspace/github_operations/ci_log_parser.py` as described below.
> Write tests first (TDD), then fix the source. Run all quality checks.
> Reference project `p_coder` at `src/mcp_coder/checks/ci_log_parser.py` is the source of truth.

## WHERE

| File | Action |
|------|--------|
| `tests/github_operations/test_ci_log_parser.py` | Update tests for 3 functions |
| `src/mcp_workspace/github_operations/ci_log_parser.py` | Fix 3 functions |

## WHAT

### 1. `_strip_timestamps(log_content: str) -> str`

**Bug**: Regex anchored with `^` — fails to strip timestamps after ANSI codes.

**Fix**: Remove `^` anchor from the regex pattern. Extract the pattern to a module-level
constant `_TIMESTAMP_PATTERN = re.compile(...)` to match p_coder's structure.

```python
# BEFORE (broken):
timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s?")
# AFTER (correct — module-level constant):
_TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s?")
```

**Test to add**: Line with ANSI prefix then timestamp — verify timestamp is stripped.

### 2. `_parse_groups(log_content: str) -> List[Tuple[str, List[str]]]`

**Bug**: `"##[group]" in line` matches false positives (e.g. line containing `see ##[group] docs`).

**Fix**: Use `line.startswith("##[group]")` and `line.startswith("##[endgroup]")`.

```python
# BEFORE (broken):
if "##[group]" in line:
# AFTER (correct):
if line.startswith("##[group]"):
```

Same for `##[endgroup]`.

**Attach-to-preceding-group behavior**: Lines that appear after `##[endgroup]` but before
the next `##[group]` must be attached to the preceding group (by updating `groups[-1]`),
NOT collected under an empty group name as mcp-workspace currently does. Read the p_coder
reference to see the exact `groups[-1]` update logic. Note that existing test
`test_handles_content_outside_groups` must be updated to expect this behavior.

**Test to add**: Line containing `##[group]` mid-line — verify it's NOT treated as group start.

### 3. `_extract_failed_step_log(log_content: str, step_name: str) -> str`

**Bug**: Only does substring match on group names, returns full log on no match.

**Fix**: Restore 3-tier matching: exact match → prefix match → contains match.
Add `##[error]` fallback. Return only error lines (not full log) when no group matches.

Port back the exact logic from p_coder reference project
`src/mcp_coder/checks/ci_log_parser.py` function `_extract_failed_step_log` using
`mcp__workspace__read_reference_file`. Key differences from current pseudocode:
1. Guard `if step_name and step_name.lower() != "unknown":` before name-based matching
2. Error fallback collects entire group sections containing `##[error]` lines (not individual lines)
3. Returns empty string when no matches and no error groups found

**Tests to add**:
- Exact match preferred over contains match
- Prefix match preferred over contains match
- `##[error]` fallback when no group matches
- Returns empty string when no group matches AND no `##[error]` lines exist

**Existing test to rewrite**: `test_returns_full_log_if_no_match` must be rewritten —
p_coder returns only `##[error]` lines (or empty string when none exist), NOT the full log.

## DATA

No changes to return types — all three functions keep their existing signatures.
