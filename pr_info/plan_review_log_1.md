# Plan Review Log — Run 1

**Issue:** #168 — Add cross-repo CI: listen to mcp-coder-utils, notify mcp_coder, add typecheck extra
**Date started:** 2026-04-28
**Branch:** 168-add-cross-repo-ci-listen-to-mcp-coder-utils-notify-mcp-coder-add-typecheck-extra
**Base:** main (up to date — no rebase needed)
**Plan files reviewed:** summary.md, step_1.md, step_2.md, step_3.md, step_4.md

---

## Round 1 — 2026-04-28

**Findings (12 raised by review subagent):**
- F1 step_2 verification doesn't assert install-step ordering (mcp-coder-utils before .[typecheck]) — load-bearing
- F2 step_2 verification doesn't assert `permissions.contents == 'read'` — least-privilege
- F3 step_2 verification doesn't assert `python-version` is the string `"3.11"` — YAML float footgun
- F4 step_3 verification doesn't assert `client-payload` keys/values
- F5 step_4 verification uses `grep -c` (CLAUDE.md mandates MCP/Grep tool over raw grep)
- F6 step_4 lacks positive `actions/checkout@v6` count assertion
- F7 steps 2/3 don't assert workflow file is at the expected path
- F8 plan files duplicate large blocks (drift risk)
- F9 step_2 hardcodes mcp-coder-utils git URL (also lives in pyproject)
- F10 verification uses bash-style continuations on Windows
- F11 step_1 lacks pre/post mypy-strict regression check
- F12 step_1 lacks defensive check that [dev] extra wasn't broken

**Decisions:**
- Auto-accept: F1, F2, F3, F4, F5, F6, F7 — defend documented load-bearing constraints or fix CLAUDE.md violation
- Skip: F8 (intentional duplication for LLM context), F9 (verbatim from issue Decisions), F10 (works under Bash tool), F11 (already covered by mandated regression block), F12 (YAGNI — keep plan simpler)

**User decisions:** none — all design decisions already locked in issue #168 Decisions table

**Changes applied:**
- `pr_info/steps/step_2.md` — extended YAML-parse one-liner with 4 new assertions: file-exists (Path), permissions.contents=='read', install-step ordering (mcp-coder-utils precedes typecheck), python-version is str "3.11"
- `pr_info/steps/step_3.md` — extended YAML-parse one-liner with file-exists assertion and JSON-parse of client-payload (assert dict, keys upstream/sha, upstream=='mcp-workspace')
- `pr_info/steps/step_4.md` — replaced four `grep -c` lines with single Python one-liner asserting substring counts (setup-uv@v8==4, setup-uv@v4==0, setup-python@v6==3, setup-python@v5==0, actions/checkout@v6==5)
- `pr_info/steps/step_1.md` — unchanged
- `pr_info/steps/summary.md` — unchanged

**Status:** committed (see commit hash via git log after commit agent runs)

---

## Round 2 — 2026-04-28

**Findings:**
- F-R2-1 step_2 verification one-liner has inline `#` comments that swallow trailing assertions and `print('OK')` after bash `\` line-continuation joins lines (CRITICAL — round-1 edits introduced this regression)
- F-R2-2 step_3 verification one-liner has same `#`-comment swallow bug for the `print('OK')`
- F-R2-3 (subset of F-R2-1) trailing `print('OK')` in step_2 dead-code due to F-R2-1
- F-R2-4 summary.md acceptance-criteria mapping doesn't cross-reference new round-1 invariants — optional

**Decisions:**
- Auto-accept: F-R2-1, F-R2-2 (and F-R2-3 resolves with F-R2-1) — critical correctness bug
- Skip: F-R2-4 — nice-to-have, doesn't block

**User decisions:** none — pure correctness fix

**Changes applied:**
- `pr_info/steps/step_2.md` — removed 3 inline `#` comments from verification one-liner (least-privilege, install-order, python-version str). Rationale already in surrounding markdown.
- `pr_info/steps/step_3.md` — removed 1 inline `#` comment from verification one-liner (payload contract).

**Status:** committed

---


## Round 3 — 2026-04-28

**Findings:** No new findings. Round-2 inline-comment strip cleanly resolved the lexer-swallow bug. Engineer traced each one-liner end-to-end (shell quoting, bash escape sequences, Python parse, JSON contract, count assertions) — no syntactic landmines remaining.

**Decisions:** N/A (no findings).

**User decisions:** none.

**Changes applied:** none — plan unchanged this round.

**Status:** clean — terminating loop.

---

## Final Status

**Rounds run:** 3
**Plan-modifying rounds:** 2 (rounds 1 and 2)
**Commits produced:**
- Round 1: `3c4c906` docs(plan): tighten plan verification one-liners (#168 review round 1)
- Round 2: `9afc7a8` docs(plan): strip inline #-comments from verification one-liners (#168 review round 2)

**Outcome:** plan ready for approval. All 4 step files verified against planning principles (one-step-one-commit, tangible results, exit criteria as green checks). Verification one-liners are mechanically correct (manual trace of shell quoting, escapes, Python lexer behavior, and substring counts against current `ci.yml`).

**Skipped findings (intentional, documented for future reference):**
- F8 — duplication between summary.md and step files (intentional for LLM context)
- F9 — hardcoded `mcp-coder-utils` git URL (verbatim from issue Decisions)
- F10 — Windows/bash continuation concern (works under Bash tool)
- F11 — pre/post mypy regression check (already covered by mandated regression block)
- F12 — defensive `[dev]` extra check (YAGNI — keeps plan simpler)
- F-R2-4 — summary.md acceptance-criteria cross-reference table (nice-to-have, doesn't block)
