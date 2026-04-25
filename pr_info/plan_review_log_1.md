# Plan Review Log — Issue #157

## Review of `verify_github()` implementation plan

## Round 1 — 2026-04-25

**Findings**:
- F1 (architecture): Plan uses single-file orchestrator instead of issue's thin orchestrator + domain helpers pattern
- F2 (correctness/critical): `required_status_checks` may return PyGithub's `NotSet` sentinel instead of `None`
- F3 (correctness/improvement): Check 2 must NOT call `get_authenticated_username()` — it discards the client needed for `oauth_scopes`
- F4 (nit): Import path for `get_repository_identifier` is from `git_operations`, not `github_operations`
- F5 (nit): Check 3 value should explicitly use `identifier.https_url`
- F6 (correctness/critical): Token `None` crashes `BaseGitHubManager` constructor and `Github(auth=...)` — breaks check independence
- F7 (architecture): `_get_repository()` is private, called from outside — by design per issue
- F8 (confirmation): `allow_force_pushes` and `allow_deletions` return `bool` directly in PyGithub — correct
- F9 (nit): Existing `_patch_get_default_branch` whitelist entry is a test fixture, different symbol
- F10 (nit): `get_default_branch` may not need whitelisting since `verify_github()` calls it

**Decisions**:
- F1: Skip — plan author's deliberate choice, documented in summary.md
- F2: Accept — add note about NotSet sentinel handling
- F3: Accept — clarify direct client creation, remove misleading import
- F4: Skip — implementer will resolve import path
- F5: Accept — small clarity improvement
- F6: Accept — add try/except blocks for independence
- F7: Skip — by design per issue
- F8: Skip — confirmation, not a finding
- F9: Skip — different symbol
- F10: Accept — make whitelist entry conditional

**User decisions**: None needed — all accepted findings were straightforward improvements.

**Changes**:
- `pr_info/steps/step_2.md`: Clarified check 2 uses direct Github client (not `get_authenticated_username()`), added try/except for check 4 when token is None, added exception handling key detail section, specified `identifier.https_url` for check 3
- `pr_info/steps/step_3.md`: Added note about `required_status_checks` NotSet sentinel
- `pr_info/steps/step_4.md`: Made `get_default_branch` vulture whitelist entry conditional

**Status**: Pending commit
