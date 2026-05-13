# Plan Review Log — Run 1

**Issue**: #198
**Date started**: 2026-05-13
**Branch**: 198-git-tool-compact-true-silently-drops-non-patch-output-stat-shortstat-numstat-name-only-name-status-and-git-show-header-lines


## Round 1 — 2026-05-13

**Findings**:
- C1 (Critical): `# Compact diff:` header placement in split-and-preserve path is wrong — pseudocode put it above the preserved prefix; should sit between prefix and compacted body.
- I1: Missing `--no-patch` tests in step_2 (git_diff) and step_3 (git_show).
- I2: Missing `--pretty=fuller` test in step_3.
- I3: Several preserves-prefix tests asserted only substring presence, not ordering.
- I4: `test_diff_compact_regression_plain_patch` was too weak — only checked `"diff --git" in result`.
- I5: Subsumed by I1 (no-patch coverage for git_diff).
- I6: Step 1 sequencing was verified — no change needed.
- Q1: `--stat=<width>` membership relies on `split("=", 1)[0]` — needed an explicit test.
- Q2: Dead-code removal (`if not output: output = plain`) in step_3 — keep as planned (subsumed by new logic).
- Q3: `compact=True` warning suppression — no change needed.
- S1–S3: skipped (helper function, naming, test granularity).

**Decisions**:
- C1, I1, I2, I3, I4, Q1: accepted — applied to plan files.
- I5: merged into I1.
- I6, Q3: no change needed (verified-only).
- Q2: accepted plan as written (dead code is correctly subsumed).
- S1–S3: skipped (cosmetic / KISS-aligned as-is).

**User decisions**: None — all findings were within scope of straightforward improvements; nothing affected architecture or feature scope.

**Changes**:
- `pr_info/steps/step_2.md`: rewrote split-and-preserve pseudocode so the `# Compact diff:` header attaches to the compacted patch portion only (after the preserved prefix). Strengthened test 6 with ordering assertion (`index("|") < index("diff --git")`). Rewrote test 7 (regression) to require multi-line staged change plus `"# Compact diff:" in result` and a `+` line. Added test 8 (`--no-patch` returns "No changes found"). Added test 9 (`--stat=80` with `split("=", 1)[0]` rationale). Updated test count 7→9.
- `pr_info/steps/step_3.md`: same pseudocode fix as step_2 (prefix / header / body ordering). Added ordering assertions to existing tests 1 (`index("Author:") < index("diff --git")`) and 9 (`index("|") < index("diff --git")`). Added test 10 (`--no-patch` preserves commit header, no `"diff --git"`). Added test 11 (`--pretty=fuller` preserves `AuthorDate:` / `CommitDate:` with ordering check). Updated test count 9→11.
- `pr_info/steps/step_1.md`: untouched.
- `pr_info/steps/summary.md`: untouched.

**Status**: Changes applied — pending commit.
