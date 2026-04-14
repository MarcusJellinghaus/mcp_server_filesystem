---
description: Code review of implementation with compact diff analysis
disable-model-invocation: true
allowed-tools:
  - "Bash(git fetch *)"
  - "Bash(git status *)"
  - "Bash(git diff *)"
  - "Bash(mcp-coder git-tool *)"
  - "Bash(mcp-coder check branch-status *)"
  - mcp__workspace__read_file
  - mcp__workspace__list_directory
  - Glob
  - Grep
---

# Implementation Review (Code Review)

**First, ensure we're up to date:**
```bash
git fetch
git status
mcp-coder check branch-status --llm-truncate
```

Confirm and display the current feature branch name.

---

**Then run the code review:**

## Code Review Request

Run this command to get the changes to review:
```bash
mcp-coder git-tool compact-diff
```

No need to run all checks; do not use pylint warnings. Feel free to further analyse any mentioned files and/or the file structure.

### Focus Areas:
- Logic errors or bugs
- Tests for `__main__` functions should be removed (not needed)
- Unnecessary debug code or print statements
- Code that could break existing functionality
- Compliance with existing architecture principles, see `docs/architecture/architecture.md`

### Output Format:
1. **Summary** - What changed (1-2 sentences)
2. **Critical Issues** - Must fix before merging
3. **Suggestions** - Nice to have improvements
4. **Good** - What works well

Do not perform any action. Just present the code review.
