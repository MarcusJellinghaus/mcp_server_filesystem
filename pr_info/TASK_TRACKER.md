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

- [x] [Step 1: Add allowlists for 7 new git commands](steps/step_1.md) — arg_validation.py + tests
- [x] [Step 2: Add new git command implementations](steps/step_2.md) — _run_simple_command, git_show, git_branch + tests
- [x] [Step 3: Unified git() dispatcher](steps/step_3.md) — dispatcher function + tests
- [x] [Step 4: Replace server tools + vulture whitelist](steps/step_4.md) — server.py, test_server.py, vulture_whitelist.py
- [x] [Step 5: Update CLAUDE.md tool mapping](steps/step_5.md) — documentation only

## Pull Request
