---
description: Refocus discussion on open requirements and feature questions
disable-model-invocation: true
---

# Issue Requirements

Refocus the conversation on open requirements after `/issue_analyse` has explored the issue and codebase.

## Instructions

Review the conversation so far and produce a structured summary:

1. **Decided items:** List what was already decided (from the issue's `## Decisions` section and the current conversation). Do not re-ask these.

2. **Questionable decisions:** If any existing decision seems risky or worth revisiting given what you've seen in the code, briefly note why. Don't block on it — just flag it.

3. **Open requirements / feature questions:** List only the remaining open questions that affect requirements or user-facing behavior. Implementation details are yours to decide — do not ask about them.

4. **Constraints & rationale identified:** List any non-obvious constraints or gotchas discovered during analysis (the "why" behind decisions, things downstream steps need to know).

**Suggested next step:** `/discuss` — to walk through the open questions one by one.
