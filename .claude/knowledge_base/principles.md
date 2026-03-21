# Engineering Principles

- **Clean Code, DRY, KISS** — encourage these consistently.
- **YAGNI** — don't build for hypothetical future requirements.
- **Test behavior, not implementation.** Cover the contract, not every corner.
- **Prefer readable code over comments.** If the code needs a comment to be understood, first try to make the code clearer. Add comments only when the *why* isn't obvious from the code itself.
- **Don't change working code for cosmetic reasons** when it's already readable.
- **If a change only matters when someone makes a future mistake, it's speculative — skip it.**
- **Code duplication should be avoided**, especially when refactoring. No need to keep old interfaces.
- **Line count estimates** — precise line numbers and line counts are not crucial. The LLM is not good at counting. Minor updates are not relevant.
- **Commit messages** — don't worry about details of commit messages. No need to clean them up if they have minor issues.
- **pr_info/ folder** — this folder will be deleted later during the process. Do not worry about it. It can be read as background information.
