---
workflow-stage: issue-discussion
suggested-next: discuss -> issue_update -> issue_approve
---

# Analyse GitHub Issue

Fetch a GitHub issue and analyze its requirements, feasibility, and potential implementation approaches.

## Instructions

First, fetch the issue details:
```bash
gh issue view $ARGUMENTS
```

Then analyze the issue:

Can we discuss this requirement / implementation idea and its feasibility?
Please also look at the code base to understand the context (using the different tools with access to the project directory).
Do not provide code yet!

At the end of our discussion, I want to have an even better issue description.

**Base Branch Handling:**
If the issue contains a `### Base Branch` section:
- Display the specified base branch prominently
- Verify the branch exists using: `git ls-remote --heads origin <branch-name>`
- If the branch does NOT exist, show a clear warning:
  "⚠️ Warning: Base branch 'X' does not exist on remote. Branch creation will fail."
- Continue with the analysis (non-blocking error)

**Focus on:**
- Understanding the problem/feature request
- Technical feasibility
- Potential implementation approaches
- Questions that need clarification
- Impact on existing code
