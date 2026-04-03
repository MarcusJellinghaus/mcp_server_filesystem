# Plan Review Log — Issue #76

## Round 1 — 2026-04-03

**Findings**:
- [Critical] Step 1: `PurePath.match()` does not support `**` recursive glob on Python 3.11 — silently breaks the most common use case
- [Critical] Step 1: Test fixture copies testdata into `tmp_path`; `list_files(".", ...)` finds those too, making exact assertions fragile
- [Critical] Step 2: `max_result_lines` counting undefined — ambiguous how lines are counted with context, and whether overlapping contexts merge
- [Critical] Step 2: `normalize_path` rationale unclear — used for security but not documented as such
- [Accept] Step 2: Opening files directly instead of `read_file` util — correct for binary skip behavior
- [Accept] Steps 1-3: Step sizing appropriate — small, testable, one commit each
- [Accept] Step 3: Wiring pattern matches existing server.py conventions
- [Skip] Step 2: Combined mode `mode` field name not explicit — low impact, inferable
- [Skip→Accept] Steps 1-2: `total_files`/`total_matches` should be pre-truncation count

**Decisions**:
- Finding 1 (PurePath): Accept — replace with `fnmatch.fnmatch()` (stdlib, works on 3.11+)
- Finding 2 (test fixtures): Accept — add guidance to use subset assertions or unique patterns
- Finding 3 (max_result_lines): Accept — define counting semantics explicitly
- Finding 9 (total counts): Accept — clarify pre-truncation semantics
- Finding 11 (normalize_path): Accept — add defense-in-depth rationale
- Finding 8 (combined mode name): Skip — implementer can infer

**User decisions**: None needed — all findings were straightforward improvements.

**Changes**:
- `pr_info/steps/step_1.md`: Replaced PurePath with fnmatch, fixed total_files to pre-truncation, added test guidance
- `pr_info/steps/step_2.md`: Defined max_result_lines counting, clarified total_matches pre-truncation, added normalize_path rationale
- `pr_info/steps/summary.md`: Updated PurePath → fnmatch in design decisions

**Status**: Ready to commit
