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

