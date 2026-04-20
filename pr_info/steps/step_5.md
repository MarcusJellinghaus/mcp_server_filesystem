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

Replace:
```markdown
| Git operations | ✅ `Bash("git ...")` | ✅ `Bash("git ...")` (allowed) |
```

With:
```markdown
| Git read-only | `Bash("git ...")` | `mcp__workspace__git()` |
| Git write (add, commit) | ✅ `Bash("git ...")` | ✅ `Bash("git ...")` (allowed) |
```

### Update Git Operations section:

Replace the `ALLOWED git operations via Bash tool` section to clarify which operations use the unified tool vs Bash:

```markdown
## 🔄 Git Operations

**Read-only git commands** — use the unified `git` MCP tool:
- `git(command="log", ...)`, `git(command="diff", ...)`, `git(command="status", ...)`
- `git(command="show", ...)`, `git(command="branch", ...)`, `git(command="fetch", ...)`
- `git(command="merge_base", ...)`, `git(command="rev_parse", ...)`
- `git(command="ls_tree", ...)`, `git(command="ls_files", ...)`, `git(command="ls_remote", ...)`

**Write git operations via Bash tool (allowed):**
- `git add`, `git commit`
```

## HOW
- Text edits only, no code changes
- Keep the existing format and style of CLAUDE.md
- Ensure the old tool names (`git_log`, `git_diff`, `git_status`, `git_merge_base`) are no longer referenced

## DATA
- No code changes, documentation only
