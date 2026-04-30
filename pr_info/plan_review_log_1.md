# Plan Review Log — Issue #176

## Round 1 — 2026-04-30

**Findings**:
- [improvement / scope] Step 6 mixes three concerns in one commit (identifier reorder + base_url to auth probe + new api_base_url CheckResult)
- [improvement / steps] Steps 4 and 5 both edit base_manager.py + test_base_manager.py
- [improvement / design] api_base_url CheckResult fallback severity="warning" rationale not explicit
- [nit / tests] TestOverallOkNotPoisonedByFallback assertion mechanism implicit
- [nit / formatting] Step 6 test helper _make_identifier couples to production hostname_to_api_base_url
- [improvement / scope] No upstream feature request filed for mcp-coder-utils replacing the local token_fingerprint helper
- [nit / tests] Step 2 known-family list ordering note (gho_/ghp_/ghs_/ghr_ all 4 chars)
- [improvement / tests] Step 7 TestRawTokenNotLogged covers only failure paths, not success path

**Decisions**:
- Step 6 cohesion: skip — cohesive bug fix, leave as-is
- Steps 4/5 split: skip — acceptable per planning principles
- severity="warning" rationale: accept (auto-fix) — add inline source comment
- TestOverallOkNotPoisonedByFallback clarity: accept (auto-fix) — make per-entry assertions explicit
- Test helper coupling: accept (auto-fix) — pass api_base_url as explicit parameter
- Upstream issue filing: escalated to user
- gho_/ghs_ ordering: skip — nit
- Raw-token negative on success path: accept (auto-fix) — extend TestRawTokenNotLogged

**User decisions**:
- Q1 (upstream issue): file the upstream feature request now, listing precise replacement targets and verifying similarity. Issue created: https://github.com/MarcusJellinghaus/mcp-coder-utils/issues/30
- Q2 (token_fingerprint design): align with prefix+suffix shape (option A). Rationale: only existing pattern in any reference project is `_mask_api_key` at p_coder/src/mcp_coder/llm/providers/langchain/verification.py:36 using `first4...last4`. Primary use case is operator self-recognition; GitHub's UI itself displays last-4 publicly. SHA-256 collision-resistance unnecessary at operator scale. Migration to upstream becomes a pure import swap.

**Changes**:
- pr_info/steps/step_2.md — full rewrite to prefix+suffix design, dropped hashlib + family list, added motivation linking to _mask_api_key and mcp-coder-utils#30
- pr_info/steps/step_6.md — added severity="warning" inline source comment; decoupled _make_identifier helper; expanded TestOverallOkNotPoisonedByFallback per-entry assertions
- pr_info/steps/step_7.md — updated expected fingerprint shape to prefix+suffix; tightened token_fingerprint conditional population; extended TestRawTokenNotLogged to cover success path
- pr_info/steps/summary.md — updated helper description, linked mcp-coder-utils#30
- pr_info/steps/Decisions.md — created; logs D1–D6

**Status**: changes applied, ready to commit

## Round 2 — 2026-04-30

**Findings**: No new findings. All Round 1 changes verified in plan files (step_2 prefix+suffix design, step_6 severity comment + decoupled test helper + explicit assertions, step_7 success-path raw-token negative, summary.md mcp-coder-utils#30 reference).

**Decisions**: N/A — nothing to fix.

**User decisions**: None requested.

**Changes**: None.

**Status**: no changes needed — loop exits.

## Final Status

- **Rounds run**: 2
- **Commits produced**: 1 (round-1 plan changes — hash 60fc93c)
- **External actions**: filed upstream feature request mcp-coder-utils#30
- **Plan readiness**: ready for approval
