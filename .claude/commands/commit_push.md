---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(black:*), Bash(isort:*), mcp__filesystem__read_file, mcp__filesystem__list_directory
workflow-stage: utility
suggested-next: (context-dependent)
---

# Commit and Push Changes

Follow this process to commit and push your changes:

## 1. Format Code
```bash
black src tests
isort --profile=black --float-to-top src tests
```

## 2. Review Changes
```bash
git status
git diff
```

## 3. Stage Changes
Stage all relevant changes (exclude any files that shouldn't be committed).

## 4. Commit
Create a commit with a clear, conventional commit message:
- Use format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Keep summary under 50 characters
- Add detailed description if needed

## 5. Push
```bash
git push
```

If the branch doesn't exist on remote yet:
```bash
git push -u origin HEAD
```
