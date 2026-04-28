# Issue #169 — GHE Cloud (`*.ghe.com`) support: API URL fix + truststore wiring

## Goal

Two related fixes for users on **GitHub Enterprise Cloud with data residency** (`*.ghe.com`), shipped together:

1. **API URL shape** — `hostname_to_api_base_url()` produces the wrong endpoint for `*.ghe.com`. The correct API base is subdomain-style (`https://api.<tenant>.ghe.com`), not GHES path-style (`https://<tenant>.ghe.com/api/v3`).
2. **Truststore wiring** — when mcp-workspace runs as a standalone MCP server behind a corporate TLS-intercepting proxy, PyGithub falls back to certifi only and SSL handshakes fail. Activate `truststore` once at the application entry point so PyGithub honors the OS trust store transitively (PyGithub → `requests` → `urllib3` → patched `ssl.SSLContext`).

Both fixes are needed for the same enterprise scenario; without either, `verify_github`, `BaseGitHubManager`, and any other PyGithub-backed code cannot work for those users.

## Architectural / Design Changes

- **No layer changes.** All edits land within existing layers; no new module crosses a boundary.
- **New utilities-layer leaf module: `mcp_workspace._ssl`.** Idempotent helper that activates `truststore` if available, no-op otherwise. Imported by `main` only.
- **Activation site = application entry point only.** `ensure_truststore()` is called inside `main()` (after `setup_logging()`, before `from mcp_workspace.server import run_server`). Never at module import time, because `truststore.inject_into_ssl()` is a global monkeypatch on `ssl.SSLContext` and library consumers (e.g. mcp-coder importing mcp-workspace) must remain free to opt in or out.
- **Hostname dispatch in `hostname_to_api_base_url()` extended from 2 branches to 3.** Lowercases the hostname before comparing (DNS is case-insensitive; git remotes can supply mixed case). Original casing preserved in the GHES fallback URL for user-visible messages. `RepoIdentifier.api_base_url` is a thin wrapper, so the fix propagates automatically — no call-site edits needed.
- **`truststore` becomes a core dependency**, not an opt-in extra. It is a small pure-Python wrapper around the stdlib; mcp-coder takes the same approach. Adding it as a core dep avoids silent SSL failures for users who don't know they need it.
- **Architecture-config touch is conditional.** `tach.toml` uses `exact = false`, and import-linter's `layers` contract only constrains listed layers. A leaf module imported only by `main` typically needs no declaration. We update these configs **only if** `tach check` or `lint-imports` flag the new module.

## Files to Create or Modify

### Created

| Path | Purpose |
|---|---|
| `src/mcp_workspace/_ssl.py` | `ensure_truststore()` helper — idempotent activation, no-op when `truststore` not importable |
| `tests/test_ssl.py` | Tests for `ensure_truststore()` — idempotent + no-op |
| `pr_info/steps/summary.md` | This file |
| `pr_info/steps/step_1.md` | Step 1: `*.ghe.com` API URL fix |
| `pr_info/steps/step_2.md` | Step 2: `_ssl.py` + `truststore` dependency |
| `pr_info/steps/step_3.md` | Step 3: Wire `ensure_truststore()` into `main()` |

### Modified

| Path | Change |
|---|---|
| `src/mcp_workspace/utils/repo_identifier.py` | Extend `hostname_to_api_base_url()`: lowercase + `*.ghe.com` branch |
| `tests/utils/test_repo_identifier.py` | Add `*.ghe.com` cases (basic + mixed-case) to `TestHostnameToApiBaseUrl` |
| `pyproject.toml` | Add `truststore` to `[project].dependencies` |
| `src/mcp_workspace/main.py` | Import + call `ensure_truststore()` in `main()` after `setup_logging()` |
| `tach.toml` | **Conditional** — declare `mcp_workspace._ssl` only if `tach check` flags it |
| `.importlinter` | **Conditional** — list `_ssl` in `layered_architecture` only if `lint-imports` flags it |

## Steps

| # | Title | Independent? |
|---|---|---|
| 1 | Fix `hostname_to_api_base_url()` for `*.ghe.com` | Yes — pure utility fix |
| 2 | Add `_ssl.py` + `truststore` dependency + tests | Yes — module is unused until step 3 |
| 3 | Wire `ensure_truststore()` into `main()` | Depends on step 2 |

Each step = one commit (tests + implementation + checks passing).

## Out of Scope

- Upstreaming `ensure_truststore()` into `mcp-coder-utils` — file as a follow-up issue per the original issue's decision table.
- Any PyGithub-specific SSL wiring — `truststore.inject_into_ssl()` patches `ssl.SSLContext` globally; PyGithub's transport (`requests` → `urllib3`) honors it transitively.
- Bare `ghe.com` (no tenant subdomain) handling — intentionally falls through to GHES path-style; not a real product hostname.
