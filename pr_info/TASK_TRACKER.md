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

### Step 1: Update Tests (TDD — Tests First) — `tests/test_reference_projects.py`

- [x] 1a. Update existing `validate_reference_projects()` calls to add `project_dir=Path("/unrelated/project")`
- [x] 1b. Update ALL `.absolute()` → `.resolve()` in test assertions across entire test file
- [x] 1c. Add parameterized overlap detection test using real temp directories (`tmp_path`)
- [x] 1d. Strengthen `test_path_normalization` assertion to check canonical path equality
- [x] Step 1 quality checks: run pylint, mypy (pytest expected to fail until Step 2)
- [x] Step 1 git commit

### Step 2: Implement Overlap Filtering in Production Code — `src/mcp_workspace/main.py`

- [x] 2a. Update `main()` — switch `project_dir` from `.absolute()` to `.resolve()`
- [x] 2b. Add `project_dir: Path` parameter to `validate_reference_projects()`
- [x] 2c. Switch reference path resolution from `.absolute()` to `.resolve()`
- [x] 2d. Add overlap checks (same dir, subdirectory, parent) after existence/directory validation
- [ ] 2e. Update call site in `main()` to pass `project_dir` to `validate_reference_projects()`
- [ ] Step 2 quality checks: run pylint, pytest, mypy — fix all issues
- [ ] Step 2 git commit

## Pull Request

- [ ] Review all changes across both steps for consistency and completeness
- [ ] Verify all quality checks pass (pylint, pytest, mypy)
- [ ] Prepare PR title and summary
