# Plan Review Log 1

**Issue**: #164
**Started**: 2026-04-27
**Branch**: 164-feat-add-polling-parameters-to-check-branch-status-mcp-tool

## Round 1 — Engineer Findings

### Strengths

- **KISS adherence is strong.** Two ~25-line private helpers with inlined terminal checks; no generic poll-abstraction; one orchestrator. Matches the issue's "Copy from p_coder" directive without over-engineering.
- **Backwards compatibility is explicit and testable.** All three new params default to no-wait; Step 3's defaults test pins this contract.
- **Step granularity respects "one step = one commit".** Each step is independently shippable: helpers (Step 1), orchestrator (Step 2), wiring (Step 3). All three exit with green pylint/pytest/mypy per Definition of done.
- **TDD ordering is concrete.** Test file path, test class names, patch targets, and assertion targets are spelled out — leaves little room for an LLM to drift.

### Findings

1. **`has_remote_tracking_branch` vs `remote_branch_exists` — issue/plan mismatch.** The issue's Decisions table says *"Check `has_remote_tracking_branch()` before PR polling"* (which queries the local branch's upstream config). Step 2 instead uses `remote_branch_exists(project_dir, branch_name)` (which lists `origin/*` refs). These are different checks: a branch can exist on origin without local tracking, and vice versa. `remote_branch_exists` is actually the more useful question here ("can a PR exist for this branch?"), but the plan should call out the deviation and justify it, or switch to `has_remote_tracking_branch`. — **Design/requirements question**

2. **Step 2 algorithm gates PR wait on `branch is not None`, but `remote_branch_exists` returns False for empty branch names already.** The pseudo-code has `if branch and not await to_thread(remote_branch_exists, ...)` followed by `elif branch:`. Two `branch` checks are redundant once we've established `branch` is truthy in the outer `if wait_for_pr:` block. Minor clarity win — flatten to one guard. — **Straightforward**

3. **Step 1 test "Tolerates 2 consecutive exceptions, then succeeds on 3rd call" — order subtle.** The current algorithm increments `errors` on exception and resets on success. The test name suggests the 3rd call succeeds; verify the test wording matches behavior: 2 raises, 3rd raises again would abort (errors == 3), but if 3rd returns success, `errors` resets and loop continues until terminal/timeout. Spell out which path is being asserted (success-after-2-fails vs abort-on-3-fails) so TDD doesn't ambiguously guide the implementer. The Step 1 list already has both cases, but the wording of the third bullet should be tightened. — **Straightforward**

4. **No test asserts `_DEFAULT_PR_TIMEOUT=600` constant value directly.** The decision table makes 600s a contract (matches CLI default). Step 2 test #3 says "called with `_DEFAULT_PR_TIMEOUT=600`" but importing the constant and asserting via `assert_awaited_with(..., 600)` is preferable — pin the constant. Recommend a parametrized test or a literal-`600` assertion. — **Straightforward**

5. **PR detection terminal check is overly loose.** `_wait_for_pr` returns when `result` is truthy (non-empty list). `find_pull_request_by_head` could in principle return a list of closed PRs. For typical use this is fine, but the original mcp_coder loop probably filters to open. Worth a one-line clarification in HOW: "Any non-empty list — including closed PRs — counts as found; the orchestrator's final `collect_branch_status` will surface PR state to the caller." — **Straightforward**

6. **Step 3 test list has 3 cases, "Definition of done" claims "all three new tests pass" — consistent, OK.** Confirm the existing `tests/test_server.py` does not currently import `check_branch_status`; if there's a sync test for it elsewhere (e.g. `tests/checks/test_branch_status.py`), grep before writing. Step 3's last bullet ("if they relied on `collect_branch_status` directly through `server.py`") is a good safety net. — **Straightforward**

7. **No mention of `CHANGELOG.md` / version bump.** The repo doesn't appear to use a CHANGELOG (none in root listing) so this is genuinely N/A. — **Skip**

8. **Logging cardinality in helpers.** Step 1 says "Log via `logger.info` / `logger.warning`". With 15s/20s intervals over 600s, that's up to 40 log lines per wait. Recommend `logger.info` at start/end only (`"Polling CI for %ss..."`, `"CI poll complete in %.1fs (status=%s)"`) and `logger.warning` only on exceptions. Avoid per-iteration `info` logs. Add this as a one-liner under HOW. — **Straightforward**

9. **`asyncio.to_thread` is Python 3.9+ — already fine** since pyproject pins `>=3.11`. No action needed. — **Skip**

10. **Missing: behavior when `ci_timeout > 0` but branch has no remote/upstream.** The plan polls CI even if the branch was never pushed. Realistically `CIResultsManager` will return empty/no-run, and `_wait_for_ci` will time out fully (e.g. 600s of fruitless polling). Consider a symmetric guard: if `ci_timeout > 0` and `not remote_branch_exists`, skip CI wait too with a recommendation. Or document the deliberate decision not to (CI can exist on any commit pushed under another branch name, etc.). — **Design/requirements question**

11. **`find_pull_request_by_head` signature.** Step 1 HOW says `PullRequestManager(project_dir).find_pull_request_by_head(branch_name)`. Worth a 30-second `list_symbols` confirmation on `pr_manager.py` to ensure that's the actual public method name. Cheap insurance against a typo that derails Step 1's TDD. — **Straightforward**

12. **No new dependencies added.** Confirmed: `pytest-asyncio>=0.25.3` already in `pyproject.toml`. No `tach.toml` or `.importlinter` changes needed (no new layer crossings). — **Skip** (correctly handled in summary).

### Overall Assessment

**The plan is close to ready, but has one open design question that should be resolved before implementation:**

- **Blocking:** Finding 1 (use `has_remote_tracking_branch` per the issue's Decisions table, or update the plan to justify using `remote_branch_exists`). This affects test fixtures in Step 2 (#3, #4, #5).
- **Should fix during plan_update (cheap):** Findings 2, 3, 4, 5, 8, 11.
- **Should ask user:** Finding 10 (CI wait without remote branch — symmetric guard or accept current behavior?).

After resolving Findings 1 and 10 and applying the small clarifications, the plan is ready to implement. The three-step structure is right-sized; no need to merge or split steps.


## Round 1 — 2026-04-27
**Findings**: (12 findings — see report below)
1. has_remote_tracking_branch vs remote_branch_exists semantic mismatch (design)
2. Redundant branch truthy guards in Step 2 (straightforward)
3. Step 1 third TestWaitForCI case ambiguous (straightforward)
4. _DEFAULT_PR_TIMEOUT import in test (straightforward)
5. _wait_for_pr terminal-check looseness needs doc (straightforward)
6. Verify no other test imports check_branch_status (straightforward)
7. No CHANGELOG (skip)
8. Logging cardinality (straightforward)
9. Python 3.11+ asyncio.to_thread (skip)
10. Asymmetric remote-branch guard for CI wait (design)
11. Confirm find_pull_request_by_head signature (straightforward)
12. No new dependencies (skip)

**Decisions**: 7 straightforward → accept; 2 design (1, 10) → escalated to user; 3 → skip
**User decisions**:
- Q1 (remote check): Use remote_branch_exists() — reason: handles push-without-upstream correctly
- Q2 (CI guard symmetry): Apply symmetric guard — skip CI polling when no remote branch, prepend push-first recommendation

**Changes**:
- step_1.md: clarified TestWaitForCI third case wording; added find_pull_request_by_head signature verification bullet; reduced logging cardinality (info on start/end, warning on exception only)
- step_2.md: switched remote check to remote_branch_exists(); moved guard to short-circuit both PR-wait and CI-wait; removed redundant branch truthy guards; pinned _DEFAULT_PR_TIMEOUT via import in test; documented _wait_for_pr terminal-state looseness; added test for ci_timeout with no remote branch
- step_3.md: made safety bullet imperative — verify no test imports check_branch_status before editing server.py
- summary.md: added note that we deviate from issue Decisions table re. remote check function; documented why

**Status**: Plan updated, ready for Round 2 review


## Round 2 — 2026-04-27
**Findings**: (4 findings)
1. Step 2 algorithm: missing explicit `branch is None` early-return before remote_branch_exists call (straightforward)
2. Step 3: verify log_function_call supports async (straightforward)
3. Step 2 test #3: contradictory mock + sleep assertion (straightforward)
4. Step 3 test: reference existing try/finally restore pattern (straightforward)

**Decisions**: all 4 → accept (straightforward)
**User decisions**: none — no design questions raised this round

**Changes**:
- step_2.md: added explicit `branch is None` early-return to algorithm; removed contradictory sleep/virtual-time assertions from orchestrator test #3
- step_3.md: added log_function_call async-support verification bullet; referenced TestGitTool::test_raises_without_project_dir as try/finally pattern source

**Status**: Plan updated, ready for Round 3 review

## Round 3 — 2026-04-27
**Findings**: (2 polish items)
1. Step 2 pseudocode: positional vs keyword max_log_lines inconsistency (straightforward)
2. Step 3 test: pr_timeout=600 equals default, ambiguous propagation assertion (straightforward)

**Decisions**: both → accept (straightforward)
**User decisions**: none

**Changes**:
- step_2.md: pseudocode uses max_log_lines=max_log_lines keyword form (matching surrounding prose)
- step_3.md: test uses non-default pr_timeout value (e.g., 120) so propagation assertion is meaningful

**Status**: Plan updated, ready for Round 4 review
