# Implementation Review Log — Issue #168

Cross-repo CI plumbing: typecheck extra, upstream-mypy-check workflow, notify-downstream workflow, action-version bump in ci.yml.

This log records each review round, triage decisions, and changes implemented.

## Round 1 — 2026-04-28

**Findings** (from `/implementation_review`):
- No critical issues. Diff is config-only (1 TOML edit + 2 new workflows + version bumps in `ci.yml`).
- Skip-candidate: `notify-downstream.yml` has no explicit `permissions:` block (auth uses PAT, not `GITHUB_TOKEN`).
- Skip-candidate: deliberate duplication of `mypy>=1.13.0` / `types-requests>=2.31.0` between `[dev]` and `[typecheck]` extras in `pyproject.toml`.
- Skip-candidate: `upstream-mypy-check.yml` uses `git+main` for `mcp-coder-utils` (no SHA pin) — by design.
- Skip-candidate: `peter-evans/repository-dispatch@v3` pinned to major tag (consistent with repo convention).
- Note: `setup-uv@v6` is intentional per commit `7fa61ce`; matches summary.md.
- Note: install order in `upstream-mypy-check.yml` (upstream `git+main` before `.[typecheck]`) is correct.
- Note: `mypy --strict src tests` invocation matches `ci.yml` matrix entry — no drift.

**Decisions**:
- All four Skip-candidates → SKIP. Each is explicitly addressed in issue #168's Decisions table:
  - "`permissions:` on `notify-downstream.yml` | Leave as proposed (no block) | Out of scope for this issue"
  - "`typecheck` vs `dev` deduplication | Keep duplicated, as proposed"
  - upstream `git+main` is the entire point of the cross-repo signal
  - Major-tag pinning matches existing `ci.yml` convention

**Verification**:
- pylint: clean | pytest: 1371 passed / 2 skipped (`-n auto`) | mypy: clean.
- All in-scope acceptance criteria met.

**Changes**: none.

**Status**: no changes needed — exit review loop.

## Final Status

- **Rounds run**: 1 (zero changes — review converged immediately)
- **Code-quality gates**: pylint, pytest (1371 passed / 2 skipped), mypy, vulture, lint-imports — all clean.
- **Architecture**: 9/9 import contracts kept.
- **Acceptance criteria**: all in-scope items satisfied; remaining items are out-of-band manual setup (`DOWNSTREAM_PAT` secret, post-merge `workflow_dispatch` smoke test) and depend on the upstream `mcp-coder-utils#28` issue.
- **Outcome**: implementation ready; no follow-up code changes required.


