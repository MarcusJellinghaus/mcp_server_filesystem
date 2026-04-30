# Decisions Log — Issue #176

This file records the design decisions agreed during plan review.

## Round 1 (plan review)

### D1. `token_fingerprint` shape: prefix+suffix (not SHA-256)

**Decision:** `format_token_fingerprint(token)` returns `f"{token[:4]}...{token[-4:]}"`
for tokens longer than 8 characters, `"****"` for tokens of length 1–8, and
`""` for empty/None input. No hashing, no GitHub-family known-prefix
allow-list, no `len=N` suffix, no `hashlib` import.

**Rationale:**
- Aligns with the existing `_mask_api_key` helper in
  `p_coder/src/mcp_coder/llm/providers/langchain/verification.py:36`.
- Matches the proposed upstream API at
  https://github.com/MarcusJellinghaus/mcp-coder-utils/issues/30, which is the
  filed feature request that will eventually replace this local helper.
- Operator recognition is the primary use case. GitHub's UI itself displays
  the last-4 publicly, so leaking it is consistent with established practice.

**Affects:** `step_2.md`, `summary.md`, `step_7.md` (test assertion shape).

### D2. Upstream replacement reference logged

**Decision:** The `summary.md` entry for the local `token_fingerprint` helper
explicitly links to mcp-coder-utils#30 as the upstream feature request that
will replace it. No other "future opportunity" hand-waving; just the issue
URL.

### D3. `severity="warning"` rationale comment in source

**Decision:** Step 6's planned source code for the `api_base_url` fallback
`CheckResult` includes a one-line comment in the Python file (not just in the
plan's prose) explaining that `severity="warning"` is chosen so the entry does
NOT poison `overall_ok` — the underlying error signal is already on
`result["repo_url"]`.

**Affects:** `step_6.md` algorithm section.

### D4. `TestOverallOkNotPoisonedByFallback` made explicit

**Decision:** The test's assertion mechanism is spelled out: assert
`overall_ok.ok is False` AND assert the contributing failure is `repo_url`
(`entries["repo_url"].ok is False, severity == "error"`), AND that
`entries["api_base_url"].ok is False` but `entries["api_base_url"].severity ==
"warning"`. The intent — proving `api_base_url` does NOT cause
`overall_ok=False` — is no longer left implicit.

**Affects:** `step_6.md` test list.

### D5. Step 6 test helper decoupled from production code

**Decision:** The `_make_identifier(...)` test helper takes `api_base_url` as
an explicit string parameter rather than calling `hostname_to_api_base_url()`.
Reason: tests should not break when the production helper's output changes.

**Affects:** `step_6.md` test helper.

### D6. Step 7 success-path raw-token negative assertion

**Decision:** `TestRawTokenNotLogged` is extended to cover the success path
(auth probe succeeds), not just the two failure paths. Asserts the raw token
does not appear in `caplog.text` nor in any `CheckResult` value/error of the
returned `result` dict. Confirms the new prefix+suffix
`format_token_fingerprint` helper does not accidentally leak the raw token
via `token_configured.token_fingerprint` on the happy path.

**Affects:** `step_7.md` test list.

## D7 — Gap A: include base_url in generic-Exception auth-probe log
Surface api_base_url in verify_github's except Exception branch so SSL/network failures on GHE hosts are diagnosable from logs alone. base_url is known at that site; adding it is a one-arg change.

## D8 — Gap B: include token fingerprint in step 4/5 DEBUG logs
Add format_token_fingerprint(self._token) to BaseGitHubManager._get_repository and get_authenticated_username DEBUG logs on GithubException. Lets operators with multiple configured tokens (env, .env, CI) disambiguate which token was used per failure. Strict raw-token negatives already in place cover the safety side.
