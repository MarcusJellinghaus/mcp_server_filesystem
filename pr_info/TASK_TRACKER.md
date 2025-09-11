# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in PR_Info/ folder

---

## Tasks

### Implementation Steps

- [x] **Step 1: CLI Argument Parsing (TDD)** - [details](steps/step_1.md)
  - Write tests for `--reference-project` CLI arguments with validation and parsing
  - Implement argument parsing with auto-rename logic for duplicates
  - Run quality checks: pylint, pytest, mypy
  - Prepare git commit

- [ ] **Step 2: Server Storage (TDD)** - [details](steps/step_2.md)
  - Write tests for global storage and initialization function
  - Implement `_reference_projects` global variable and `set_reference_projects()` function
  - Update `run_server()` signature to accept reference projects
  - Run quality checks: pylint, pytest, mypy
  - Prepare git commit

- [ ] **Step 3: Discovery MCP Tool (TDD)** - [details](steps/step_3.md)
  - Write tests for `get_reference_projects()` MCP tool
  - Implement tool for LLM discovery of available reference projects
  - Run quality checks: pylint, pytest, mypy
  - Prepare git commit

- [ ] **Step 4: Directory Listing MCP Tool (TDD)** - [details](steps/step_4.md)
  - Write tests for `list_reference_directory()` MCP tool
  - Implement tool to list files in reference projects with gitignore filtering
  - Run quality checks: pylint, pytest, mypy
  - Prepare git commit

- [ ] **Step 5: File Reading MCP Tool (TDD)** - [details](steps/step_5.md)
  - Write tests for `read_reference_file()` MCP tool
  - Implement tool to read files from reference projects with security validation
  - Run quality checks: pylint, pytest, mypy
  - Prepare git commit

- [ ] **Step 6: CLI to Server Integration (TDD)** - [details](steps/step_6.md)
  - Write tests for integration between CLI argument parsing and server initialization
  - Implement integration in `main()` function to pass reference projects to server
  - Run quality checks: pylint, pytest, mypy
  - Prepare git commit

- [ ] **Step 7: Documentation** - [details](steps/step_7.md)
  - Update README.md with reference project functionality
  - Document new CLI arguments, MCP tools, and usage examples
  - Run quality checks: pylint, pytest, mypy
  - Prepare git commit

### Feature Completion

- [ ] **PR Review**
  - Review entire pull request for the feature using `tools/pr_review.bat`
  - Address any issues found during review
  - Run final quality checks: pylint, pytest, mypy
  - Prepare final git commit if needed

- [ ] **PR Summary Creation**
  - Create comprehensive feature summary using `tools/pr_summary.bat`
  - Generate PR description for external review
  - Clean up PR_Info folder (remove steps/, clear tasks from TASK_TRACKER.md)

