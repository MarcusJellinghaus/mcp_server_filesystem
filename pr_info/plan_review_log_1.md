# Plan Review Log — Issue #197

**Issue:** edit_file: diff output is malformed — missing header newlines and absolute paths with double slash
**Branch:** 197-edit-file-diff-output-is-malformed-missing-header-newlines-and-absolute-paths-with-double-slash
**Started:** 2026-05-12

This log tracks plan review rounds for issue #197. Each round appends a `## Round {r}` section.


## Round 1 — 2026-05-12

**Findings:**
- (Improvement) Merge `step_1.md` and `step_2.md` — both defects share one root cause (`_create_diff` helper); per `planning_principles.md` ("Merge tiny or intertwined steps") they belong in one commit.
- (Improvement) Header-newline test assertion is brittle — should assert `"\n+++ "` and `"\n@@ "` substrings (behavior-focused) rather than splitlines counting.
- (Improvement) Forward-slash normalization is untested on Linux CI — need a parametrized backslash input case (`"sub\\dir\\test_file.py"`) so the `.replace("\\", "/")` line is actually exercised.
- (Improvement) `summary.md` and step prompts use incorrect pytest phrasing ("fast-unit-test marker exclusion") — CLAUDE.md prescribes `mcp__mcp-tools-py__run_pytest_check` with `extra_args: ["-n", "auto"]`.
- (Nit) Drifting line-number references in step prompts — replaced with behavior-named call-site descriptions.
- (Nit, skipped) Improving the existing `test_basic_replacement` to use `project_dir` — out of scope (YAGNI).

**Decisions:**
- All four improvements: accepted.
- Drifting line-numbers nit: accepted (cheap, durable).
- Existing-test refactor nit: skipped — YAGNI, expands scope beyond the bug fix.

**User decisions:** none — no design/requirements questions surfaced (all four decisions in issue body are reflected in plan).

**Changes:**
- Deleted `pr_info/steps/step_2.md`.
- Rewrote `pr_info/steps/step_1.md` as a single merged step covering: dropping `lineterm=""`, normalizing `filename` with `.replace("\\", "/")`, switching three `_create_diff` call sites from `str(abs_path)` to `file_path`. Two regression tests specified: Test A (header-newline substring assertions); Test B (parametrized over `"test_file.py"` and `"sub\\dir\\test_file.py"`).
- Updated `pr_info/steps/summary.md`: 2 steps → 1 step; pytest phrasing corrected to `mcp__mcp-tools-py__run_pytest_check` with `extra_args: ["-n", "auto"]`; rationale citing `planning_principles.md` added.

**Status:** plan changes applied — committing this round, then re-reviewing.

## Round 2 — 2026-05-12

**Findings:**
- (Critical) Factual error: plan claimed `_create_diff` has three call sites, including a non-existent "position-aware return". Source verification shows only two call sites — line 60 (empty-old-string prepend return) and line 84 (normal-replace return). The position-aware already-applied branch returns the literal string `"No changes needed - edit already applied"` and does NOT call `_create_diff`.

**Decisions:**
- Critical finding: accepted.

**User decisions:** none.

**Changes:**
- `step_1.md`: corrected LLM Prompt, WHERE section, Source-changes item 3, and ALGORITHM comment from "three" to "two"; added clarifying note that the position-aware already-applied branch returns a literal string and does not call `_create_diff`.
- `summary.md`: corrected Fix-overview prose (~5 lines → ~4 lines), table row (added behavior labels and position-aware clarification), Files-modified table ("+ 3 call sites" → "+ 2 call sites"), and Implementation-steps bullet.
- Verified remaining "three" occurrences (the three diff header lines and the three quality checks) are unrelated and correct — left alone.

**Status:** plan changes applied — committing this round, then re-reviewing.

## Round 3 — 2026-05-12

**Findings:**
- (Critical) None.
- (Improvements) None actionable.
- (Design / Requirements) None.
- (Nits) None worth changing.

**Decisions:** N/A — zero findings.

**User decisions:** none.

**Changes:** none — plan unchanged this round.

**Status:** ready for approval — loop terminates.

## Final Status

- **Rounds run:** 3
- **Commits produced:**
  - `4f5eb81` — plan(#197): merge step_1 and step_2 into single step for _create_diff fix
  - `7572db4` — plan(#197): correct _create_diff call-site count from three to two
  - Final log commit (this commit) — plan(#197): finalize review log
- **Plan state:** ready for implementation approval. One step (`pr_info/steps/step_1.md`), one commit's worth of work, ~4 source lines + 2 regression tests in `tests/file_tools/test_edit_file.py`.
- **Outstanding questions for user:** none.
