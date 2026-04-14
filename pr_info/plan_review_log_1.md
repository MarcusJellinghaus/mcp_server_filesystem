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

**Status**: pending commit
