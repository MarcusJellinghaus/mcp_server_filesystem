---
allowed-tools: Bash(gh issue create:*)
workflow-stage: issue-discussion
suggested-next: discuss -> issue_update -> issue_approve
---

# Create GitHub Issue

Based on our prior discussion, create a GitHub issue.

**Instructions:**
1. Extract the issue title and body from the conversation context
2. Use a clear, descriptive title
3. Include relevant details from our discussion in the body
4. Use markdown formatting for better readability

**Optional: Base Branch**
If the feature should be based on a branch other than the default (main/master), include:

```markdown
### Base Branch

<branch-name>
```

Use cases:
- Hotfixes based on release branches
- Features building on existing work
- Long-running feature branches

**Important:** Before specifying a base branch, verify it exists:
```bash
git ls-remote --heads origin <branch-name>
```

If no base branch is needed, omit this section entirely.

**Create the issue using:**
```bash
gh issue create --title "TITLE" --body "BODY"
```

If no prior discussion context is found, respond: "No discussion context found. Please discuss the feature or bug first before creating an issue."
