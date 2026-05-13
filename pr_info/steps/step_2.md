# Step 2 — Fix `git_diff()` compact rendering for non-patch and combined flags

## Goal

Stop `git_diff(compact=True)` from silently dropping non-patch output and from losing the `--stat` block when combined with `-p`. Introduces the `_NON_PATCH_FLAGS` frozenset that Step 3 will reuse.

## WHERE

- `src/mcp_workspace/git_operations/read_operations.py`:
  - Add a new module-level constant `_NON_PATCH_FLAGS` near the existing `_SAFETY_FLAGS`.
  - Rewrite the body of the `if compact:` block inside `git_diff()` (currently at approximately lines 140–178).
- `tests/git_operations/test_read_operations.py`:
  - Add tests under the existing `TestGitDiff` class (`@pytest.mark.git_integration`, uses `git_repo_with_commit`).

## WHAT

No public signature changes. New private constant:

```python
_NON_PATCH_FLAGS: frozenset[str] = frozenset(
    {"--stat", "--shortstat", "--numstat",
     "--name-only", "--name-status", "--no-patch"}
)
```

`git_diff()` keeps its current signature:

```python
def git_diff(
    project_dir: Path,
    args: Optional[list[str]] = None,
    pathspec: Optional[list[str]] = None,
    search: Optional[str] = None,
    context: int = 3,
    max_lines: int = 100,
    compact: bool = True,
) -> str
```

## HOW

- No new imports.
- Inline flag detection inside `git_diff()` (no helper function).
- When non-patch-only flags are present, set `compact = False` locally so execution falls through to the existing non-compact `else` branch — reuses code, no `-M -C90%` injection, one git call.
- Otherwise, after fetching plain output, split at the first `diff --git` line; preserve the prefix; compact only the patch portion; rebuild as `prefix + compacted`.

## ALGORITHM

Pseudocode for the rewritten `if compact:` block inside `git_diff()`:

```
1. has_non_patch = any(a in _NON_PATCH_FLAGS or a.split("=",1)[0] in _NON_PATCH_FLAGS for a in user_args)
   has_patch     = "-p" in user_args or "--patch" in user_args
   if has_non_patch and not has_patch:
       skip the compact block → use the existing else (plain) branch
2. final_args = strip --color* from user_args
   final_args = ["-M", "-C90%"] + final_args
   plain = repo.git.diff(_SAFETY_FLAGS + final_args + pathspec_tail)
   if not plain: return "No changes found"
3. idx = plain.find("diff --git")
   prefix, patch_portion = (plain[:idx].rstrip("\n"), plain[idx:]) if idx >= 0 else (plain, "")
4. if not patch_portion:
       output = prefix            # nothing to compact (rare; non-patch fallback)
   else:
       ansi      = repo.git.diff("--color=always", "--color-moved=dimmed-zebra", _SAFETY_FLAGS + final_args + pathspec_tail)
       compacted = render_compact_diff(patch_portion, ansi)
       if not compacted: compacted = patch_portion
       # IMPORTANT: the "# Compact diff: orig_n → new_n" header (when compaction
       # reduced the line count) is prepended to the COMPACTED PATCH PORTION
       # ONLY — never to the whole output. The line counts reflect only the
       # patch portion, so the header must sit between the preserved prefix
       # and the compacted diff body, not at the very top.
       if compaction reduced patch line count:
           compacted = f"# Compact diff: {orig_n} → {new_n} lines …\n" + compacted
       # Final ordering:
       #   <preserved prefix lines>
       #   <# Compact diff header, if any>
       #   <compacted diff body>
       output = prefix + "\n" + compacted if prefix else compacted
```

The post-block `if not output: return "No changes found"`, `search`, and `truncate_output()` calls remain unchanged.

## DATA

- `_NON_PATCH_FLAGS: frozenset[str]` — module-level constant.
- `git_diff()` return value: still `str` — the descriptive message, raw diff, or compacted output as before, but now never silently empty for the affected flag combinations.

## Tests to write (TDD)

In `tests/git_operations/test_read_operations.py`, inside `TestGitDiff`, add (all `@pytest.mark.git_integration`, fixture `git_repo_with_commit`):

1. `test_diff_compact_stat_returns_output` — modify a file, call `git_diff(project_dir, args=["--stat"])`, assert result is **not** `"No changes found"` and contains `"README.md"` and `"|"` (the stat separator).
2. `test_diff_compact_shortstat_returns_output` — similar with `--shortstat`; assert `"changed"` or `"insertion"` in result.
3. `test_diff_compact_numstat_returns_output` — similar with `--numstat`; assert digits and `"README.md"` present.
4. `test_diff_compact_name_only_returns_output` — similar with `--name-only`; assert `"README.md"` in result.
5. `test_diff_compact_name_status_returns_output` — similar with `--name-status`; assert a status letter (e.g. `"M"`) and `"README.md"`.
6. `test_diff_compact_stat_and_patch_preserves_prefix` — call with `args=["--stat", "-p"]`; assert both the stat summary (e.g. `"|"`) and a `"diff --git"` line are present, AND assert **ordering**: `result.index("|") < result.index("diff --git")` (the `|` is the stat-row separator and must appear before the patch body). Add a brief test comment: the prefix-before-patch invariant is what the split-and-preserve logic guarantees.
7. `test_diff_compact_regression_plain_patch` — create a commit, then stage a *multi-line* change in a working file so the compact algorithm has something to compact (e.g. add ~5 unchanged context lines surrounded by 2 changed lines). Call with default args. Assert `"diff --git" in result` (patch survived) **and** `"# Compact diff:" in result` (proves the compactor actually ran on the patch portion) **and** that a changed line (e.g. `"+new line"`) is present (proves the patch wasn't dropped by the rebuild).
8. `test_diff_compact_no_patch_returns_no_changes_marker` — stage changes in a working file, then call `git_diff(project_dir, args=["--no-patch"], compact=True)`. Assert the result is exactly `"No changes found"` because `--no-patch` suppresses the diff payload (non-patch-only flag → bypass branch → empty plain output → descriptive marker).
9. `test_diff_compact_stat_with_width_argument` — call `git_diff(project_dir, args=["--stat=80"], compact=True)` against a repo with staged changes. Assert the result is **not** `"No changes found"` and contains `"|"`. This exercises the `a.split("=", 1)[0] in _NON_PATCH_FLAGS` membership check (proves that flags with `=<value>` such as `--stat=80` are still recognised as non-patch flags and routed through the bypass).

Brief note for the implementer: the `a.split("=", 1)[0]` membership check exists specifically because git accepts `--stat=<width>`, `--stat=<width>,<name>`, and similar parameterised forms — bare-string membership against `_NON_PATCH_FLAGS` would otherwise miss them.

Write tests first, see them fail (or skip), implement, see them pass.

## HOW the bypass reuses existing code

Rather than duplicating the else-branch logic, set a local `compact = False` (or break out of the `if compact:` early) so the existing non-compact path executes unchanged.

## Verification

After implementation, run all three MCP checks:

- `mcp__tools-py__run_pytest_check` with `-n auto` and the standard "not …_integration" exclusion (the new tests are `git_integration`-marked; run those separately with `markers=["git_integration"]` to confirm).
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`

All must pass.

## Commit

One commit: new tests + `_NON_PATCH_FLAGS` constant + rewritten `if compact:` block in `git_diff()`.

## LLM prompt

> Implement Step 2 as specified in `pr_info/steps/step_2.md`. Use `pr_info/steps/summary.md` as context for the overall fix and the rationale behind `_NON_PATCH_FLAGS`. Follow TDD: write the nine `TestGitDiff` integration tests first, confirm they fail, then add the `_NON_PATCH_FLAGS` frozenset and rewrite the `if compact:` block of `git_diff()` in `src/mcp_workspace/git_operations/read_operations.py`. Do not modify `compact_diffs.py`. Do not introduce helper functions — keep the flag check inline. Run all three MCP code-quality checks (pytest with the recommended exclusions plus a follow-up `markers=["git_integration"]` run, pylint, mypy) and ensure they pass before producing exactly one commit. Use only MCP tools as required by `.claude/CLAUDE.md`.
