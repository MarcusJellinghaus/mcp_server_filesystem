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

**Fix**: Remove `^` anchor from the regex pattern.

```python
# BEFORE (broken):
timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s?")
# AFTER (correct):
timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s?")
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

**Test to add**: Line containing `##[group]` mid-line — verify it's NOT treated as group start.

### 3. `_extract_failed_step_log(log_content: str, step_name: str) -> str`

**Bug**: Only does substring match on group names, returns full log on no match.

**Fix**: Restore 3-tier matching: exact match → prefix match → contains match.
Add `##[error]` fallback. Return only error lines (not full log) when no group matches.

```python
# Pseudocode:
for group_name, lines in groups:
    if group_name.lower() == step_name.lower():       # exact
        return "\n".join(lines)
for group_name, lines in groups:
    if group_name.lower().startswith(step_name.lower()):  # prefix
        return "\n".join(lines)
for group_name, lines in groups:
    if step_name.lower() in group_name.lower():        # contains
        return "\n".join(lines)
# Fallback: return only ##[error] lines
error_lines = [l for l in log_content.split("\n") if "##[error]" in l]
return "\n".join(error_lines) if error_lines else log_content
```

**Tests to add**:
- Exact match preferred over contains match
- Prefix match preferred over contains match
- `##[error]` fallback when no group matches
- Returns full log only when no `##[error]` lines exist either

## DATA

No changes to return types — all three functions keep their existing signatures.
