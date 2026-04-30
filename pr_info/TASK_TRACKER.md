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

### Step 1: Add `_diagnostics.py` shared helper module
See [step_1.md](./steps/step_1.md) for details.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Add `token_fingerprint.py` utility
See [step_2.md](./steps/step_2.md) for details.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: DEBUG logging in `hostname_to_api_base_url()`
See [step_3.md](./steps/step_3.md) for details.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: DEBUG companion in `BaseGitHubManager._get_repository()`
See [step_4.md](./steps/step_4.md) for details.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: DEBUG in `get_authenticated_username()` GithubException path
See [step_5.md](./steps/step_5.md) for details.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: `verify_github` bug fix — identifier-first order, `base_url` to auth probe, `api_base_url` result entry
See [step_6.md](./steps/step_6.md) for details.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: `verify_github` diagnostics — split-except, DEBUG, `token_fingerprint` field
See [step_7.md](./steps/step_7.md) for details.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review (self-review of diff, address feedback)
- [ ] PR summary (description, linked issue #176, test evidence)
