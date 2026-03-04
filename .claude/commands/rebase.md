---
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git fetch:*), Bash(git rebase:*), Bash(git add:*), Bash(git commit:*), Bash(git push --force-with-lease:*), Bash(git diff:*), Bash(git checkout --ours:*), Bash(git checkout --theirs:*), Bash(git rebase --abort:*), Bash(black:*), Bash(isort:*), mcp__code-checker__run_all_checks, mcp__code-checker__run_pylint_check, mcp__code-checker__run_pytest_check, mcp__code-checker__run_mypy_check, mcp__filesystem__read_file, mcp__filesystem__edit_file
workflow-stage: utility
suggested-next: (context-dependent)
---

# Rebase Branch onto Main

Rebase the current feature branch onto main and resolve conflicts.

**Core philosophy:** Main is the source of truth. The feature branch adapts to main. For conflicts, preserve main's improvements and rework the feature branch code to fit.

**Note on `--ours`/`--theirs` during rebase:** `--ours` = main (the branch being rebased onto), `--theirs` = feature branch commits being replayed.

## Pre-flight Checks (Abort if any fail)

1. Working directory is clean (`git status` shows no uncommitted changes)
2. Not already in rebase/merge state
3. Not on main/master branch
4. Remote origin exists

## Workflow

1. `git fetch origin`
2. `git rebase origin/main`
3. For each conflict:
   - Resolve manually, preserving main's improvements
   - Rework feature branch changes to fit
   - Verify no conflict markers remain
   - `git add <file>`
   - `git rebase --continue`
4. Format code:
   ```bash
   black src tests
   isort --profile=black --float-to-top src tests
   ```
5. Run code checks: `mcp__code-checker__run_pytest_check`, `mcp__code-checker__run_pylint_check`, `mcp__code-checker__run_mypy_check`
6. Fix any issues from merge
7. Report summary and ask for user confirmation
8. `git push --force-with-lease`

## Conflict Resolution Strategies

| File Type | Strategy |
|-----------|----------|
| Code files (`.py`) | Keep both sides, merge imports, preserve main's structure |
| Test files | Keep all tests from both sides |
| Config files (`pyproject.toml`) | Merge additively, prefer main for conflicts |
| Lockfiles | Accept theirs (`--theirs`), notify user |

## Abort Rules (in priority order)

1. Any unexpected error - abort, report full error
2. Binary file conflict - abort, cannot auto-resolve
3. Conflict markers remain after resolution - abort
4. Same file conflicts 3+ times - abort
5. Code quality fails after 2 fix attempts - abort

On abort: run `git rebase --abort`, report which rule triggered, suggest next steps.
