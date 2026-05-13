# Step 3 — Fix `git_show()` compact rendering for prefix preservation

## Goal

Stop `git_show(compact=True)` from silently dropping the commit header and other pre-patch output (`--stat` block, `--oneline`, `--format`, `--pretty` lines). Apply the same fix shape as Step 2 and remove the dead `if not output: output = plain` rescue that is no longer needed.

## WHERE

- `src/mcp_workspace/git_operations/read_operations.py`:
  - Rewrite the body of the `if compact and not has_colon:` block inside `git_show()` (currently at approximately lines 317–340).
  - Remove the `if not output: output = plain` rescue (currently approximately line 330).
- `tests/git_operations/test_read_operations.py`:
  - Add tests under the existing `TestGitShow` class.

## WHAT

No public signature changes:

```python
def git_show(
    project_dir: Path,
    args: Optional[list[str]] = None,
    pathspec: Optional[list[str]] = None,
    search: Optional[str] = None,
    context: int = 3,
    max_lines: int = 100,
    compact: bool = True,
) -> str
```

Reuses `_NON_PATCH_FLAGS` introduced in Step 2.

## HOW

- No new imports (constant lives in the same module).
- Same inline flag-detection idiom as in `git_diff()`.
- Bypass: non-patch-only flags fall through to the existing non-compact `else` branch.
- Patch path: split plain output at first `diff --git`, preserve prefix, compact only the patch portion.
- Remove the dead `if not output: output = plain` rescue — every case it handled is now covered by the split-and-prefix logic.

## ALGORITHM

Pseudocode for the rewritten `if compact and not has_colon:` block:

```
1. has_non_patch = any(a in _NON_PATCH_FLAGS or a.split("=",1)[0] in _NON_PATCH_FLAGS for a in user_args)
   has_patch     = "-p" in user_args or "--patch" in user_args
   if has_non_patch and not has_patch:
       skip the compact block → use the existing else (plain) branch
2. final_args = strip --color* from user_args; prepend ["-M", "-C90%"]
   plain = repo.git.show(_SAFETY_FLAGS + final_args + pathspec_tail)
   if not plain: return "No output."
3. idx = plain.find("diff --git")
   prefix, patch_portion = (plain[:idx].rstrip("\n"), plain[idx:]) if idx >= 0 else (plain, "")
4. if not patch_portion:
       output = prefix            # no diff payload — just the header/summary
   else:
       ansi      = repo.git.show("--color=always", "--color-moved=dimmed-zebra", _SAFETY_FLAGS + final_args + pathspec_tail)
       compacted = render_compact_diff(patch_portion, ansi)
       if not compacted: compacted = patch_portion
       # IMPORTANT: the "# Compact diff: orig_n → new_n" header (when compaction
       # reduced the line count) is prepended to the COMPACTED PATCH PORTION
       # ONLY — never to the whole output. The line counts reflect only the
       # patch portion, so the header must sit between the preserved commit
       # header / pre-patch summary and the compacted diff body, not at the
       # very top above the commit header.
       if compaction reduced patch line count:
           compacted = f"# Compact diff: {orig_n} → {new_n} lines …\n" + compacted
       # Final ordering:
       #   <preserved prefix lines (commit header, stat summary, oneline/format/pretty output)>
       #   <# Compact diff header, if any>
       #   <compacted diff body>
       output = prefix + "\n" + compacted if prefix else compacted
```

The post-block `if not output: return "No output."`, `search`, and `truncate_output()` calls remain unchanged. The `if not output: output = plain` rescue is **removed**.

## DATA

- `git_show()` return value: still `str` — descriptive message, raw output, or compacted output as before, but now the commit header / pre-patch prefix is always preserved.

## Tests to write (TDD)

In `tests/git_operations/test_read_operations.py`, inside `TestGitShow`, add (all `@pytest.mark.git_integration`, fixture `git_repo_with_commit`):

1. `test_show_compact_preserves_commit_header` — call `git_show(project_dir, args=["HEAD"])`; assert the result contains `"Author:"` and `"Date:"` (commit header) **and** `"diff --git"` (patch), AND assert **ordering**: `result.index("Author:") < result.index("diff --git")` (commit header must appear before the patch body). Comment the test to explain the prefix-before-patch invariant.
2. `test_show_compact_oneline_preserved` — call with `args=["--oneline", "HEAD"]`; assert the result contains the commit subject `"Initial commit"`.
3. `test_show_compact_format_preserved` — call with `args=["--format=%H", "HEAD"]`; assert the result contains a 40-hex-char commit SHA.
4. `test_show_compact_stat_returns_output` — call with `args=["HEAD", "--stat"]`; assert result is **not** `"No output."` and contains `"|"` (stat separator).
5. `test_show_compact_shortstat_returns_output` — analogous, `--shortstat`.
6. `test_show_compact_numstat_returns_output` — analogous, `--numstat` (depends on Step 1 allowlist change).
7. `test_show_compact_name_only_returns_output` — analogous, `--name-only`.
8. `test_show_compact_name_status_returns_output` — analogous, `--name-status`.
9. `test_show_compact_stat_and_patch_preserves_prefix` — call with `args=["HEAD", "--stat", "-p"]`; assert both `"|"` (stat) and `"diff --git"` are present, AND assert **ordering**: `result.index("|") < result.index("diff --git")` (stat block must appear before the patch body). Comment the test to make the prefix-before-patch invariant explicit.
10. `test_show_compact_no_patch_preserves_commit_header` — call `git_show(project_dir, args=["HEAD", "--no-patch"], compact=True)`. Assert the commit header lines (`"Author:"` and `"Date:"`, plus a subject/SHA line) are present in the result, **and** that `"diff --git"` is NOT in the result (the `--no-patch` flag suppresses the diff payload; the bypass branch preserves the commit header as the entire output).
11. `test_show_compact_pretty_preserved` — call `git_show(project_dir, args=["HEAD", "--pretty=fuller"], compact=True)`. Assert a fuller-format-only field is present in the prefix (e.g. `"AuthorDate:"` or `"CommitDate:"`) **and** that `"diff --git"` still appears after the prefix in the result (assert ordering: `result.index("AuthorDate:") < result.index("diff --git")`).

The existing `test_show_compact_default` and `test_show_head_commit` tests should continue to pass (regression).

Write tests first, see them fail, implement, see them pass.

## Verification

After implementation, run all three MCP checks:

- `mcp__tools-py__run_pytest_check` with `-n auto` and the standard "not …_integration" exclusions, followed by `markers=["git_integration"]` to confirm new tests pass.
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`

All must pass.

## Commit

One commit: new tests + rewritten `if compact and not has_colon:` block in `git_show()` + deletion of the dead rescue.

## LLM prompt

> Implement Step 3 as specified in `pr_info/steps/step_3.md`. Use `pr_info/steps/summary.md` as context and reuse the `_NON_PATCH_FLAGS` frozenset introduced in Step 2. Follow TDD: write the eleven `TestGitShow` integration tests first, confirm they fail, then rewrite the `if compact and not has_colon:` block of `git_show()` in `src/mcp_workspace/git_operations/read_operations.py` and remove the now-dead `if not output: output = plain` rescue. Do not modify `compact_diffs.py`. Keep the flag check inline (no helper function). Run all three MCP code-quality checks (pytest with the recommended exclusions plus a follow-up `markers=["git_integration"]` run, pylint, mypy) and ensure they pass before producing exactly one commit. Use only MCP tools as required by `.claude/CLAUDE.md`.
