# Planning Principles

## Step Design

- **Merge tiny or intertwined steps.** Steps that are trivially small or tightly coupled should be combined. However, prefer several small steps over fewer large ones — small steps fit better in LLM context windows.
- **Split large steps.** Ideally each step can be completed such that pylint/pytest/mypy still pass afterward.
- **One step = one commit.** Each step should produce exactly one commit: write tests, implement, verify checks pass. If a step needs multiple fix-and-commit cycles, split it into smaller steps.
- **No separate "fix all issues" steps.** Quality checks passing is an exit criterion for each step, not a separate step.
- **No "verify everything" cleanup steps.** If each step leaves checks green, a final verification step is unnecessary. If you find yourself planning one, the earlier steps are too large.
- **Every step must have tangible results.** No preparation steps like "read docs" or "explore codebase" — analysis happens as part of implementation.
- **No need to fill in task tracker during planning.** This is done automatically as step 0 of implementation.
- **No rollback options needed.** Don't plan for how to undo steps.

## Testing

- **No manual tests.** All tests must be automated.
- **Test structure mirrors src structure.** Tests for `src/foo/bar.py` go in `tests/foo/test_bar.py`.
- **Parameterized tests** are a good idea to reduce the number of required test functions while covering more cases.

## Code Quality

- **If uncertain about the codebase, analyze it.** Don't guess — read the code and understand before planning changes.
- **If a question implies worsening code quality**, include small refactorings in the plan to actually improve it.

## Documentation

- **Docstrings** should document functions well, without examples.
- **CLI commands** should be documented via CLI help text and in the `docs/` folder.
