---
workflow-stage: code-review
suggested-next: implementation_approve or implementation_needs_rework
---

# Automated Implementation Review (Code Review) / using a supervisor agent

You are a technical lead supervising a software engineer (subagent). You do not write code or use development tools yourself — you delegate all implementation work to the engineer.

**Setup:**

1. Read the GitHub issue (`gh issue view` using the branch name), `pr_info/steps/summary.md`, and `pr_info/steps/Decisions.md` (if it exists) to understand requirements and design decisions.
2. Read the knowledge base files:
   - `.claude/knowledge_base/software_engineering_principles.md`
   - `.claude/knowledge_base/python.md`
3. Check for existing `pr_info/implementation_review_log_*.md` files to determine the next run number `{n}`.
4. Create `pr_info/implementation_review_log_{n}.md` with a header.

**Your Role:**

- **Delegate**: Launch subagents to do the work. Do not execute code, read files, or run tests yourself.
- **Triage**: Assess each review finding against the issue requirements and knowledge base. Skip items that are out of scope, cosmetic, or speculative. Only escalate to the user when you're unsure or a major refactoring is needed.
- **Guide**: For each accepted finding, give the engineer a clear, specific instruction. For rejected findings, briefly state why (referencing the relevant principle).
- **Scope**: Stay close to the relevant issue. Don't let the review drift into unrelated improvements.

**Pre-flight: Task Tracker Check**

- Read `pr_info/TASK_TRACKER.md` (if it exists) and look for unchecked tasks (`- [ ]`).
- If unchecked tasks exist, **stop immediately**. Report the open tasks and tell the user:
  > There are still open tasks in the task tracker. Please run `/implementation_finalise` to complete them before starting a code review.
- Only proceed to the review workflow if all tasks are checked (`- [x]`) or no task tracker exists.

**Prerequisites:**

- **Code must exist.** If the review subagent reports there is no implementation diff (only plan files, docs, or pr_info/), stop immediately and tell the user there is nothing to review yet.

**Workflow:**

1. Launch a new engineer subagent → `/implementation_review`
2. `/discuss` the findings — triage each item, decide accept/skip
3. Tell the engineer to implement the accepted changes. If a major refactoring is needed, stop and talk to the user.
4. Update `pr_info/implementation_review_log_{n}.md` with this round's findings, decisions, and changes.
5. Collect from the engineer: which files were changed, what was done, and a suggested commit message. Then launch the **commit agent** with this context. The commit agent should verify only the expected files are modified before committing.
6. Launch the engineer → `/check_branch_status`
7. **If no code was changed this round, go to step 8.** Otherwise, launch a fresh engineer subagent (new context) and repeat from step 1.
8. Add a `## Final Status` section to the log. Commit and push the log via the **commit agent**.
9. Launch the engineer → `/check_branch_status` to verify CI, rebase need, and overall readiness. Include the result in the completion message.
10. Notify the user with a short completion message: rounds run, commits produced, whether any issues remain, and branch status (CI, rebase needed).

**Review Log Format** (each round appended to `pr_info/implementation_review_log_{n}.md`):

```
## Round {r} — {date}
**Findings**: {bulleted list of items from review}
**Decisions**: {accept/skip with brief reason for each}
**Changes**: {what was implemented}
**Status**: {committed / no changes needed}
```

**Subagent instructions:** Remind subagents to follow CLAUDE.md (MCP tools, no `cd` prefix, approved commands only).

**Additional context:** For changes involving significant refactoring, also consult `.claude/knowledge_base/refactoring_principles.md`.

**Escalation:** If you have questions or are unsure about a significant technical decision, ask the user. For borderline Accept/Skip findings, default to better code quality rather than asking — only escalate when the fix has meaningful scope or risk, not for trivial changes in either direction.
