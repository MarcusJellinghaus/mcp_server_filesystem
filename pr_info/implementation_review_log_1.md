# Implementation Review Log 1

**Branch:** 170-verify-github-expose-token-source-in-checkresult-to-disambiguate-env-var-vs-config-file-precedence
**Started:** 2026-04-28

## Round 1 — 2026-04-28

**Findings**:
- [Minor] `verification.py:50` — `Github(auth=Auth.Token(None))` constructed when token is `None`. Pre-existing behavior; reviewer notes it's out of scope.
- [Nit] `verification.py:81-86` — `if source is not None` guard is redundant per the helper's `Literal["env","config"] | None` contract when `token is not None`.
- [Nit] `TASK_TRACKER.md` — `PR review` and `PR summary` boxes unchecked.

**Decisions**:
- SKIP — Out of scope for issue 170; pre-existing; reviewer concurs.
- SKIP — Python's type system does not statically correlate tuple elements, so the runtime guard remains meaningful as defensive code; reviewer notes it's "arguably more defensive against future helper changes". Trivial either way; not worth a code touch.
- SKIP — Intentionally unchecked; handled at PR-finalization stage.

**Quality Gates**:
- pylint: PASS
- pytest (in-scope tests): PASS — 49/49 tests in `tests/test_config.py` + `tests/github_operations/test_verification.py`. One unrelated pre-existing failure noted in `tests/github_operations/test_github_utils.py::test_pr_manager_lifecycle` (untouched by this branch).
- mypy: PASS

**Implementation alignment with issue 170**:
- `get_github_token_with_source()` added in `config.py` with correct signature.
- `get_github_token()` now delegates to the new helper (single source of truth).
- `CheckResult.token_source: NotRequired[Literal["env", "config"]]` extended in `verification.py`.
- `token_configured` double-write collapsed to a single assignment.
- `token_source` populated whenever a token resolves (incl. on auth failure); omitted when no token.
- 4 new helper tests + 4 new `TestTokenSource` tests, including the motivating auth-failure case.
- 13 mock-patch sites mechanically updated.
- `get_test_repo_url()` deferred (YAGNI).

**Changes**: None — all findings skipped on triage.

**Status**: No changes needed; proceed to step 8 quality checks.

## Final Status

**Rounds run:** 1 (zero code changes — all findings skipped on triage)

**Quality gates (final):**
- pylint: PASS
- pytest (in-scope): PASS — 49/49
- mypy: PASS
- vulture: PASS — no output (supervisor-run)
- lint-imports: PASS — 9 contracts kept, 0 broken (supervisor-run)

**Issue 170 acceptance:**
- `get_github_token_with_source()` helper added (`src/mcp_workspace/config.py`); `get_github_token()` delegates to it.
- `CheckResult.token_source: NotRequired[Literal["env", "config"]]` added (`src/mcp_workspace/github_operations/verification.py`).
- `token_source` populated for every token-resolving path including auth failure; omitted when no token.
- `token_configured` double-write collapsed to a single end-of-function assignment.
- Tests cover env / config / precedence / neither / auth-failure-with-source.
- `get_test_repo_url()` correctly deferred (YAGNI).

**Outcome:** No code changes required. Implementation faithfully matches issue 170 scope and design. Ready for PR finalization.
