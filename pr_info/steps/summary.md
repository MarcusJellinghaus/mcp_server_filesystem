# Issue #176 — `verify_github` GHE auth-probe fix + DEBUG diagnostics

## Overview

Two coupled fixes in one PR:

1. **Bug fix** — `verify_github()` constructs its auth-probe `Github` client without `base_url`, so it always hits `api.github.com` regardless of the repo's host. GHE tokens are rejected there with `401 Bad credentials`, contradicting the repo-access check (which uses the right host). Fix: resolve the repo identifier first, then pass `api_base_url` into the auth probe. Fall back to `api.github.com` when the identifier cannot be resolved.

2. **Observability** — On failure, DEBUG logs do not show HTTP status, response body, diagnostic headers, or which API URL each probe hit. Add failure-path DEBUG at three sites (auth probe, `_get_repository`, `get_authenticated_username`) plus a single happy-path DEBUG in `hostname_to_api_base_url()` (its decision is not visible elsewhere).

The downstream consumer (`mcp-coder verify`) renders the new fields, so DEBUG is reserved for irreplaceable failure-only detail (status, body, headers, fingerprint).

## Architectural / Design Changes

### New utility helpers (small, single-purpose, pure)

- **`mcp_workspace.github_operations._diagnostics`** — frozenset allow-list of 7 response headers + `extract_diagnostic_headers(exc)` helper. Three call-sites need the same allow-list and exception formatting; centralizing avoids drift. Underscore prefix marks it as package-private.
- **`mcp_workspace.utils.token_fingerprint`** — `format_token_fingerprint(token)`: pure function, no I/O. Returns `<prefix>...XXXX, len=N` (or `<malformed>, len=N` for `len<8`). Local helper (not upstreamed) — acknowledged trade-off vs. the project's "no local workarounds" guideline; future upstreaming opportunity.

### Result-dict shape (`verify_github`)

- New first key: `api_base_url: CheckResult`
  - identifier resolved → `ok=True`, `severity="error"`, value = URL
  - identifier failed → `ok=False`, `severity="warning"` (does **not** poison `overall_ok` — `repo_url` already reports the underlying error), value mentions fallback
- `token_configured: CheckResult` gains optional `token_fingerprint: NotRequired[str]` populated whenever a token loaded
- Final dict order: `api_base_url`, `authenticated_user`, `token_configured`, `repo_url`, `repo_accessible`, branch protection checks (5–9), `auto_delete_branches`, `overall_ok`

### Control flow (`verify_github`)

- Identifier resolution moves to the **front** of the function (auth probe now depends on `api_base_url`)
- Auth probe `except` is **split** into two clauses:
  - `except GithubException` → DEBUG-log status, data, headers (allow-listed), api_base_url, token_fingerprint
  - `except Exception` → DEBUG-log only `str(exc)` (network/SSL errors lack status/data/headers)
- Each clause still produces its own `CheckResult`. Independence of checks is preserved.

### DEBUG logging (failure-path focused)

- `hostname_to_api_base_url()` — happy-path DEBUG (input, normalized, branch, URL). Its decision is invisible elsewhere.
- `verify_github` auth probe — split-except DEBUG via `_diagnostics`
- `BaseGitHubManager._get_repository()` — `GithubException` DEBUG companion alongside existing user-friendly ERROR
- `get_authenticated_username()` — `GithubException` DEBUG before re-raising as `ValueError`

### Why these are not duplicate logs

The three failure-path DEBUG sites are independent HTTP calls (auth probe → `/user`, `_get_repository` → `/repos/owner/repo`, `get_authenticated_username` → `/user` from a different caller surface). Each deserves its own log line. The shared helper (`_diagnostics`) ensures the header allow-list and formatter live in exactly one place.

### Architecture / contracts (no changes)

- `mcp_workspace.utils` is already a leaf layer in `tach.toml` — `token_fingerprint.py` fits.
- `_diagnostics.py` lives inside `github_operations`, which is already authorized to import `github`.
- No `.importlinter` or `tach.toml` changes needed.

## Files to Create

| Path | Purpose |
|---|---|
| `src/mcp_workspace/github_operations/_diagnostics.py` | `DIAGNOSTIC_HEADERS` constant + `extract_diagnostic_headers(exc)` |
| `src/mcp_workspace/utils/token_fingerprint.py` | `format_token_fingerprint(token)` |
| `tests/github_operations/test_diagnostics.py` | Tests for `extract_diagnostic_headers` |
| `tests/utils/test_token_fingerprint.py` | Tests for `format_token_fingerprint`, including raw-token-not-in-output negative |
| `pr_info/steps/summary.md` | This document |
| `pr_info/steps/step_1.md` … `step_7.md` | Per-step implementation prompts |

## Files to Modify

| Path | Change |
|---|---|
| `src/mcp_workspace/utils/repo_identifier.py` | Add module logger + DEBUG log in `hostname_to_api_base_url()` |
| `src/mcp_workspace/github_operations/base_manager.py` | DEBUG companion in `_get_repository` (GithubException); split `except` in `get_authenticated_username` (GithubException → DEBUG → `ValueError`) |
| `src/mcp_workspace/github_operations/verification.py` | Reorder identifier first; add `api_base_url` result entry; pass `base_url` to auth-probe `Github(...)`; split auth `except`; add DEBUG; add `token_fingerprint` to `token_configured`; extend `CheckResult` TypedDict with `token_fingerprint` |
| `tests/utils/test_repo_identifier.py` | Add substring `caplog.text` checks for DEBUG output |
| `tests/github_operations/test_base_manager.py` | Add substring DEBUG checks for `_get_repository` and `get_authenticated_username` failure paths; raw-token-not-in-logs negatives |
| `tests/github_operations/test_verification.py` | Constructor-kwarg base_url assertions (github.com + GHE); `api_base_url` result shape (success + fallback); `token_fingerprint` field; substring DEBUG checks for both `except` branches; raw-token-not-in-logs negatives |

## Step Sequence (7 steps, each = 1 commit)

| # | Step | Touched files |
|---|---|---|
| 1 | Add `_diagnostics.py` (constant + extractor) | `_diagnostics.py`, `test_diagnostics.py` |
| 2 | Add `token_fingerprint.py` | `token_fingerprint.py`, `test_token_fingerprint.py` |
| 3 | DEBUG in `hostname_to_api_base_url()` | `repo_identifier.py`, `test_repo_identifier.py` |
| 4 | DEBUG in `_get_repository()` GithubException path | `base_manager.py`, `test_base_manager.py` |
| 5 | DEBUG in `get_authenticated_username()` GithubException path | `base_manager.py`, `test_base_manager.py` |
| 6 | `verify_github` bug fix: identifier-first order, `base_url` to auth probe, `api_base_url` result entry | `verification.py`, `test_verification.py` |
| 7 | `verify_github` diagnostics: split-except, DEBUG, `token_fingerprint` field | `verification.py`, `test_verification.py` |

## Test Conventions (from issue)

- Substring assertions via `caplog.text` (`"status=401" in caplog.text`) — never exact-string pinning
- One strict assertion: raw token never appears in any log/output
- Use `caplog.set_level(logging.DEBUG, logger="<module>")` inline in tests that need DEBUG capture
- GHE-fix proof: assert on `mock_github_class.call_args.kwargs["base_url"]`, not by simulating a wrong-host rejection
