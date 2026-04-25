# Summary: Add `verify_github()` for GitHub Connectivity & Branch Protection Verification

**Issue:** #157

## Goal

Add a `verify_github(project_dir: Path)` function that returns a structured dict covering GitHub connectivity and branch protection checks. All checks use PyGithub — no `gh` CLI dependency. Exposed as a Python function only (no MCP tool).

## Design / Architecture Changes

### New public API

| Symbol | Location | Description |
|--------|----------|-------------|
| `CheckResult` | `github_operations/verification.py` | TypedDict for per-check results |
| `verify_github(project_dir)` | `github_operations/verification.py` | Orchestrator — runs all 9 checks, returns dict |
| `get_default_branch()` | `github_operations/base_manager.py` | New method on `BaseGitHubManager` — exposes `repo.default_branch` |

### Architecture pattern

Single-file orchestrator in `verification.py`. No separate verify_* helper functions in `config.py` or `base_manager.py` — the orchestrator calls existing functions directly (`get_github_token()`, `get_repository_identifier()`, `BaseGitHubManager._get_repository()`) and creates a direct `Github` client for auth/scopes (not `get_authenticated_username()`, which discards the client). This keeps all verification logic in one readable file.

`get_default_branch()` is the only addition to `base_manager.py` because it's explicitly required as public API for external callers beyond verification.

### Key design decisions

- **`oauth_scopes` ordering**: `get_user()` must be called before reading `Github.oauth_scopes` (populated by first API call). The orchestrator handles this internally.
- **Branch protection batch**: Checks 5–9 share a single `get_protection()` call. A 404 means no protection — all five report `ok: False` as warnings.
- **Two-tier severity**: `overall_ok` reflects only error-severity checks (1–4). Branch protection is warning-only.
- **Independence**: Each check runs and reports regardless of earlier failures.
- **No architecture config changes**: `verification.py` lives inside `github_operations/` which already has correct layer assignments in `.importlinter` and `tach.toml`.

## Files Created or Modified

### New files

| File | Purpose |
|------|---------|
| `src/mcp_workspace/github_operations/verification.py` | `CheckResult` TypedDict + `verify_github()` orchestrator |
| `tests/github_operations/test_verification.py` | Unit tests (all mocked, no real GitHub calls) |

### Modified files

| File | Change |
|------|--------|
| `src/mcp_workspace/github_operations/base_manager.py` | Add `get_default_branch()` method |
| `src/mcp_workspace/github_operations/__init__.py` | Export `verify_github`, `CheckResult` |
| `vulture_whitelist.py` | Add `verify_github`, `get_default_branch`, `CheckResult` |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Add `get_default_branch()` to `BaseGitHubManager` + tests | `feat: add get_default_branch() to BaseGitHubManager` |
| 2 | Add `CheckResult` TypedDict + `verify_github()` orchestrator (checks 1–4: token, auth, repo URL, repo access) + tests | `feat: add verify_github() with connectivity checks` |
| 3 | Add branch protection checks (5–9) to `verify_github()` + tests | `feat: add branch protection checks to verify_github()` |
| 4 | Export from `__init__.py`, update vulture whitelist | `chore: export verify_github and update whitelist` |
