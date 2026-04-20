# Step 5: Update CLAUDE.md Tool Mapping

## Context
See [summary.md](./summary.md) for full context. This step updates the CLAUDE.md tool mapping table to reflect the unified `git` tool.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md for context.
Implement Step 5: update .claude/CLAUDE.md to replace references to the 4 old git tools with the unified git tool.
Run all three quality checks after.
```

## WHERE
- `.claude/CLAUDE.md` — update tool mapping table and git operations section

## WHAT

### Update tool mapping table:

In the `### Tool mapping` table, replace the 4 individual git rows:
```markdown
| Git log | `mcp__workspace__git_log` |
| Git diff | `mcp__workspace__git_diff` |
| Git status | `mcp__workspace__git_status` |
| Git merge-base | `mcp__workspace__git_merge_base` |
```

With a single row:
```markdown
| Git (read-only) | `mcp__workspace__git` |
```

### Update `## Git operations` section:

Replace:
```markdown
**Prefer MCP tools** for read-only git operations: `mcp__workspace__git_log`, `mcp__workspace__git_diff`, `mcp__workspace__git_status`, `mcp__workspace__git_merge_base`. These run without permission prompts.

**`git_diff` includes compact diff by default** — detects moved code, collapses unchanged blocks. Use `compact=False` for raw output. For code review, prefer `mcp__workspace__git_diff` over `mcp-coder git-tool compact-diff`.

**Bash commands** for git operations that have no MCP equivalent:

\`\`\`
git commit / fetch / ls-tree / show
gh issue view / gh pr view / gh run view
mcp-coder check branch-status
mcp-coder check file-size --max-lines 750
mcp-coder gh-tool set-status <label>
\`\`\`
```

With:
```markdown
**Prefer MCP tools** for read-only git operations: use `mcp__workspace__git` with the `command` parameter (log, diff, status, merge_base, show, branch, fetch, rev_parse, ls_tree, ls_files, ls_remote). These run without permission prompts.

**`git(command="diff")` includes compact diff by default** — detects moved code, collapses unchanged blocks. Use `compact=False` for raw output.

**Bash commands** for git operations that have no MCP equivalent:

\`\`\`
git commit / git add
gh issue view / gh pr view / gh run view
mcp-coder check branch-status
mcp-coder check file-size --max-lines 750
mcp-coder gh-tool set-status <label>
\`\`\`
```

## HOW
- Text edits only, no code changes
- Keep the existing format and style of CLAUDE.md
- Ensure the old tool names (`git_log`, `git_diff`, `git_status`, `git_merge_base`) are no longer referenced

## DATA
- No code changes, documentation only
