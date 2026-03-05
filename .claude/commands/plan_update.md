---
workflow-stage: plan-review
suggested-next:
  - commit_push -> plan_approve
  - commit_push -> /clear -> plan_review
---

# Update Plan Files

Update the implementation plan files in `pr_info/steps` based on our discussion.

## Instructions

Update the plan by modifying the different files in folder `pr_info/steps`
Please do targeted changes.

Please log the decisions from our discussion in `pr_info/steps/Decisions.md`.
Only put those decisions that we discussed, no invented decisions.
(For each decision that you log, consider whether you discussed it with me and when I said so)

**Guidelines:**
- Make minimal, focused changes
- Preserve existing structure where possible
- Ensure consistency across all step files
- Update the summary if scope changes
