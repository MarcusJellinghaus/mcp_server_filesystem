# Step 1: Refactor `get_latest_commit_sha()` to Use GitPython

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: replace the `execute_command` subprocess call in `get_latest_commit_sha()` with GitPython's `safe_repo_context`. Run all code quality checks after making changes.

## WHERE

- **Modify**: `src/mcp_workspace/git_operations/commits.py`

## WHAT

Rewrite `get_latest_commit_sha(project_dir: Path) -> Optional[str]`:
- Use `safe_repo_context` (already imported in the file) instead of `execute_command`
- Remove the `execute_command` import line — no other usages remain in this file

## HOW

- `safe_repo_context` is already imported from `.core`
- `InvalidGitRepositoryError` and `GitCommandError` are already imported from `git.exc`
- Existing tests in `tests/git_operations/test_commits.py::TestGetLatestCommitSha` validate the contract — no test changes needed

## ALGORITHM

```
def get_latest_commit_sha(project_dir):
    try:
        with safe_repo_context(project_dir) as repo:
            return repo.head.commit.hexsha
    except (InvalidGitRepositoryError, GitCommandError, ValueError, OSError):
        return None
```

`ValueError` covers empty repos / detached HEAD with no commits.
`OSError` covers non-existent or inaccessible paths.

## DATA

- **Input**: `project_dir: Path`
- **Output**: `Optional[str]` — 40-char hex SHA or `None`
- **Contract preserved**: returns `None` on any failure

## VERIFICATION

- Existing tests pass without modification (`TestGetLatestCommitSha`: 3 tests)
- pylint, mypy, pytest all pass

## COMMIT

`refactor: replace execute_command with GitPython in get_latest_commit_sha`
