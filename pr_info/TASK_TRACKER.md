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

### Step 1: Add `typecheck` extra to `pyproject.toml`

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Pylint check passes — fix all issues
- [x] Pytest passes — fix all issues
- [x] Mypy check passes — fix all issues
- [x] Commit message prepared

### Step 2: Create `.github/workflows/upstream-mypy-check.yml`

Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code)
- [x] Pylint check passes — fix all issues
- [x] Pytest passes — fix all issues
- [x] Mypy check passes — fix all issues
- [x] Commit message prepared

### Step 3: Create `.github/workflows/notify-downstream.yml`

Detail: [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code)
- [x] Pylint check passes — fix all issues
- [x] Pytest passes — fix all issues
- [x] Mypy check passes — fix all issues
- [x] Commit message prepared

### Step 4: Bump action versions in `.github/workflows/ci.yml`

Detail: [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code)
- [x] Pylint check passes — fix all issues
- [x] Pytest passes — fix all issues
- [x] Mypy check passes — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review (address feedback, resolve comments)
- [ ] PR summary prepared
