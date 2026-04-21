# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Fix algorithm + update existing tests

- [ ] Implementation: reverse distance direction, remove early-exit, add default-branch tiebreaker, update 2 existing test mocks ([step_1.md](./steps/step_1.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Add 4 new regression tests

- [ ] Implementation: add `test_selects_main_over_dormant_feature_branch`, `test_prefers_default_branch_on_equal_distance`, `test_includes_candidate_at_threshold`, `test_distance_zero_collects_all_candidates` ([step_2.md](./steps/step_2.md))
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review complete
- [ ] PR summary prepared
