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

- [x] [Step 1: Promote git_operations to top-level](steps/step_1.md) — move source + tests, update all imports
- [ ] [Step 2: Add infrastructure files](steps/step_2.md) — config.py, constants.py, utils/timezone_utils.py + tests
- [ ] [Step 3: Move github_operations source](steps/step_3.md) — copy from mcp_coder, adjust imports, add PyGithub dep
- [ ] [Step 4: Move github_operations tests](steps/step_4.md) — copy from mcp_coder, adjust fixtures, register marker
- [ ] [Step 5: Architecture enforcement + CI](steps/step_5.md) — .importlinter, tach.toml, CI split, full verification

## Pull Request
