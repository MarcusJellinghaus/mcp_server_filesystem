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

### Step 1: Fix `hostname_to_api_base_url()` for `*.ghe.com`

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Add `_ssl.py` helper + `truststore` dependency

Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code, including `tach.toml` and `.importlinter` updates)
- [x] Quality checks: pylint, pytest, mypy, tach, lint-imports — fix all issues
- [x] Commit message prepared

### Step 3: Wire `ensure_truststore()` into `main()`

Detail: [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code, including `tach.toml` update)
- [x] Quality checks: pylint, pytest, mypy, tach, lint-imports — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review
- [ ] PR summary
