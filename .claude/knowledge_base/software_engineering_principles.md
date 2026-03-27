# Software Engineering Principles

## Quality Baseline

- **Every change should leave the code better than before.** Not just "no worse" — actively better. This is the expectation, not a stretch goal.
- **Boy Scout Rule** — when you touch a file, look for one small improvement: fix a misleading name, remove dead code you just created, clean an import you just changed. One good deed per PR, not a renovation.
- **Don't change working code for cosmetic reasons** when it's already readable.

## Code Review Scope

- **Pre-existing issues are out of scope.** Note them if important, but don't block the review or create fix-up work. File a separate issue if needed.
- **Review findings fall into three buckets:**
  1. **Critical** — must fix before merge (bugs, regressions, security)
  2. **Accept** — worth fixing now, bounded effort (Boy Scout fixes)
  3. **Skip** — cosmetic, speculative, or pre-existing
- **If a change only matters when someone makes a future mistake, it's speculative — skip it.**

## Code Style

- **Clean Code, DRY, KISS** — encourage these consistently.
- **YAGNI** — don't build for hypothetical future requirements.
- **Test behavior, not implementation.** Cover the contract, not every corner.
- **Prefer readable code over comments.** If the code needs a comment to be understood, first try to make the code clearer. Add comments only when the *why* isn't obvious from the code itself.
- **Code duplication should be avoided**, especially when refactoring. No need to keep old interfaces.

## Don't Worry About

- **Line count estimates** — precise line numbers and line counts are not crucial. The LLM is not good at counting. Minor updates are not relevant.
- **Commit messages** — no need to clean them up if they have minor issues.
- **pr_info/ folder** — deleted later during the process. Can be read as background information.
