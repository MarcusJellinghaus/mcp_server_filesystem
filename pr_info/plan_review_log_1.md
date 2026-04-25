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

**Status**: Committed (ce33190)

## Round 2 — 2026-04-25

**Findings**:
- F1 (improvement): `allow_force_pushes`/`allow_deletions` could also be NotSet — add defensive note
- F2 (critical): Step 3 pseudocode missing explicit `repo is None` guard around `manager.get_default_branch()`
- F3 (improvement): `required_status_checks` NotSet handling over-complicated — simple `None` check suffices
- F4 (nit): `github_token=None` doesn't prevent second `get_github_token()` call — misleading comment
- F5 (nit): `Auth.Token(None)` raises AssertionError specifically
- F6 (nit): Confirmation check 2 independence works — already addressed

**Decisions**:
- F1: Accept — add defensive None handling note for force push/deletions
- F2: Accept — make guard explicit in pseudocode
- F3: Accept — simplify to plain `None` check, avoid private import
- F4: Accept — fix misleading comment
- F5: Skip — caught by Exception, not worth documenting
- F6: Skip — already addressed in round 1

**User decisions**: None needed.

**Changes**:
- `pr_info/steps/step_3.md`: Added explicit `if repo is None` guard in algorithm, simplified required_status_checks guidance, added defensive note for allow_force_pushes/allow_deletions
- `pr_info/steps/step_2.md`: Fixed misleading github_token comment

**Status**: Pending commit
