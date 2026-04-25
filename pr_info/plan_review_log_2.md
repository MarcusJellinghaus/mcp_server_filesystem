# Plan Review Log 2 — Issue #156 (GHE URL Support)

## Round 1 — 2026-04-25

**Findings**:
- I3: Step 2 says "If completely empty, delete the file" for `github_utils.py` — vague, could leave orphaned imports causing lint errors
- I4: `TestGithubTokenForwarding` patch update listed in both Step 2 and Step 3 — confusing for implementer
- I6: `from_full_name` hostname parameter backward-compat — verified correct
- I7: `tach.toml` dependency addition — verified architecturally correct
- M1-M6: Line references, docstring updates, exception handling — all verified correct
- No critical issues found (0 build-breaking problems)

**Decisions**:
- Accept (I3): Replace vague deletion instruction with explicit "delete `github_utils.py` entirely"
- Accept (I4): Clarify in Step 3 that `TestGithubTokenForwarding` patch updates were already done in Step 2
- Skip (I6, I7, M1-M6): Verified correct, no changes needed

**User decisions**: None needed — both fixes are straightforward clarity improvements.

**Changes**:
- `pr_info/steps/step_2.md`: Explicit deletion instruction for `github_utils.py`
- `pr_info/steps/step_3.md`: Clarified `TestGithubTokenForwarding` section — patch updates done in Step 2

**Status**: Committed (ddbe988)

## Round 2 — 2026-04-25

**Findings**:
- Step 3's `TestGithubTokenForwarding` section has bullet "Remove assertions on `_repo_owner`, `_repo_name`, `_repo_full_name`" but the class has NO such assertions — incorrect instruction
- Step 2's HOW implementation order has `github_utils.py` deletion (step 4) before `__init__.py` update (step 5), but `__init__.py` imports from `github_utils.py` — would break if run between sub-steps
- Steps 1 and 4 unaffected by round 1 changes — verified clean

**Decisions**:
- Accept (incorrect bullet): Remove second bullet from `TestGithubTokenForwarding` section in Step 3
- Accept (HOW order): Swap steps 4 and 5 — update `__init__.py` before deleting `github_utils.py`

**User decisions**: None needed.

**Changes**:
- `pr_info/steps/step_3.md`: Removed incorrect `_repo_owner`/`_repo_name`/`_repo_full_name` bullet from `TestGithubTokenForwarding`
- `pr_info/steps/step_2.md`: Swapped HOW steps 4↔5 — `__init__.py` update before `github_utils.py` deletion

**Status**: Committing
