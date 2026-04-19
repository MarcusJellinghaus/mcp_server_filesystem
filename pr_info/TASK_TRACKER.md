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

- [x] [Step 1](steps/step_1.md) — Git primitives: `get_remote_url()` and `clone_repo()` in `remotes.py`
- [x] [Step 2](steps/step_2.md) — `reference_projects.py`: ReferenceProject dataclass, URL normalizer, URL verifier
- [x] [Step 3](steps/step_3.md) — `reference_projects.py`: `ensure_available()` with async locking and failure cache
- [x] [Step 4](steps/step_4.md) — `main.py` + `server.py`: KV CLI parser, URL verification, data model migration
- [ ] [Step 5](steps/step_5.md) — `server.py`: async handlers + `ensure_available()` integration
- [ ] [Step 6](steps/step_6.md) — `server.py`: `search_reference_files()` tool + API response update
- [ ] [Step 7](steps/step_7.md) — Config files: `.importlinter`, `tach.toml`, `vulture_whitelist.py`, `.mcp.json`

## Pull Request
