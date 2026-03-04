---
allowed-tools: Bash(git fetch:*), Bash(git status:*), Bash(git diff:*), Bash(mcp-coder check branch-status:*), Bash(mcp-coder git-tool compact-diff:*), mcp__filesystem__read_file, mcp__filesystem__list_directory
workflow-stage: code-review
suggested-next: commit_push
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

Get the changes to review:
```bash
mcp-coder git-tool compact-diff
```

No need to run all checks manually - the CLAUDE.md file requires all quality checks to pass after every change.

### Focus Areas:
- Logic errors or bugs
- MCP protocol compliance and best practices
- Unnecessary debug code or print statements
- Code that could break existing functionality
- Type safety (mypy strict compliance)
- Test coverage for new functionality

### Output Format:
1. **Summary** - What changed (1-2 sentences)
2. **Critical Issues** - Must fix before merging
3. **Suggestions** - Nice to have improvements
4. **Good** - What works well

Do not perform any action. Just present the code review.
