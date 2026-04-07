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

### Step 1: Parameter validation in `read_file`
> [Detail](./steps/step_1.md) — Add `start_line`, `end_line`, `with_line_numbers` params and strict input validation

- [x] Implementation: tests + production code
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Line-range slicing with streaming
> [Detail](./steps/step_2.md) — Replace `f.read()` with `enumerate(file)` streaming, return only requested lines

- [x] Implementation: tests + production code
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: `with_line_numbers` formatting
> [Detail](./steps/step_3.md) — Implement smart-default `with_line_numbers` and dynamic-width `N→content` prefixes

- [x] Implementation: tests + production code
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Server wrapper updates + forwarding test
> [Detail](./steps/step_4.md) — Expose new params in MCP tools (`read_file`, `read_reference_file`), update tests, update README

- [x] Implementation: tests + production code
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request
- [ ] PR review: all steps complete and checks green
- [ ] PR summary prepared
