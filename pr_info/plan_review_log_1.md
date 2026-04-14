# Plan Review Log — Issue #94

Modernize reinstall_local.bat to match mcp-coder pattern.

## Round 1 — 2026-04-14
**Findings**:
- ERROR: Reference project `p_tools` does not exist — must be `p_mcp_utils`
- ERROR: Function signature `main(project_dir)` doesn't match actual reference `main()`
- ERROR: Test reference file `tests/test_read_github_deps.py` doesn't exist in any reference project
- ERROR: Pytest `-m` marker filters will fail with `--strict-markers` (markers undefined in mcp-workspace)
- INCONSISTENCY: Summary table step count/packages wrong for reference project
- INCONSISTENCY: `mcp-config` vs `mcp-config-tool` in summary table
- IMPROVEMENT: Contradictory signature vs "copy verbatim" instruction
- QUESTION: CLI verification is enhancement over p_mcp_utils template (acceptable)

**Decisions**:
- Accept fixes 1-5, 7, 9 (all straightforward corrections)
- Skip #6 (uninstall list is correct for mcp-workspace, just differs from reference)
- Skip #8 (CLI check is a good addition, no change needed)
- No design questions to escalate

**User decisions**: none needed

**Changes**:
- Replaced all `p_tools` → `p_mcp_utils` in summary.md, step_1.md, step_2.md
- Fixed function signature to `def main() -> None:` in step_1.md
- Changed test file from "adapted from reference" to "written from scratch" in step_1.md
- Removed pytest `-m` marker filters from verification commands in step_1.md and step_2.md
- Fixed Key Adaptation Points table in summary.md (steps, uninstall list, import/CLI checks)

**Status**: committed (0a7989a)

## Round 2 — 2026-04-14
**Findings**:
- Minor: step_2.md "adapt by removing" bullets referenced p_coder steps that don't exist in p_mcp_utils
- Minor: overview mentioned "no LangChain/MLflow" which is p_coder framing, not relevant to p_mcp_utils
- All round 1 fixes verified correct
- Planning principles check: all pass

**Decisions**:
- Accept both minor fixes (straightforward corrections to match p_mcp_utils reference)

**User decisions**: none needed

**Changes**:
- Rewrote "adapt by" bullets in step_2.md to reflect actual differences from p_mcp_utils (not p_coder)
- Fixed overview line in step_2.md

**Status**: committed (0f53aca)

## Round 3 — 2026-04-14
**Findings**:
- Minor: summary.md table still had "no LangChain/MLflow" qualifier in target column
- Minor: step_2.md LLM prompt still referenced removing LangChain/MLflow and multi-CLI checks
- All other checks passed

**Decisions**:
- Accept both (last remnants of p_coder framing)

**User decisions**: none needed

**Changes**:
- Removed "no LangChain/MLflow" from summary.md table
- Simplified LLM prompt adapt-by instruction in step_2.md

**Status**: committed (18f9570)

## Round 4 — 2026-04-14
**Findings**: none
**Status**: plan is ready for implementation

## Round 4 — 2026-04-14
**Findings**: none
**Status**: plan clean — then reference projects renamed (`p_checker` → `p_tools`, `p_mcp_utils` → `p_coder-utils`)

## Round 5 — 2026-04-14
**Findings**: none — rename applied correctly, no stale references
**Status**: plan is ready for implementation

## Final Status

- **Rounds**: 5 (3 with fixes, 1 rename, 1 clean verification)
- **Commits**: 4 (`0a7989a`, `0f53aca`, `18f9570`, `2e7685c`)
- **Plan status**: ready for implementation approval
- **No design questions** were escalated — all findings were straightforward corrections
