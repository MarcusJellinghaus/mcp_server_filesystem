# Step 3: Add github_token Passthrough to CIResultsManager

**Commit**: `fix: add github_token passthrough to CIResultsManager`

## Context
See [summary.md](summary.md) for full issue context.
This is the smallest change — `CIResultsManager.__init__` is missing the `github_token`
parameter that `BaseGitHubManager` already supports. One source fix, one test.

## LLM Prompt
> Read `pr_info/steps/summary.md` and this file. Add the `github_token` parameter to
> `CIResultsManager.__init__` and add a passthrough test. Run all quality checks.

## WHERE

| File | Action |
|------|--------|
| `tests/github_operations/test_ci_results_manager_foundation.py` | Add 1 test |
| `src/mcp_workspace/github_operations/ci_results_manager.py` | Fix `__init__` signature |

## WHAT

### Source: `CIResultsManager.__init__`

```python
# BEFORE:
def __init__(
    self, project_dir: Optional[Path] = None, repo_url: Optional[str] = None
) -> None:
    super().__init__(project_dir=project_dir, repo_url=repo_url)

# AFTER:
def __init__(
    self,
    project_dir: Optional[Path] = None,
    repo_url: Optional[str] = None,
    github_token: Optional[str] = None,
) -> None:
    super().__init__(project_dir=project_dir, repo_url=repo_url, github_token=github_token)
```

Update docstring Args section to include `github_token`.

### Test: `test_github_token_passthrough`

```python
def test_github_token_passthrough(self) -> None:
    """Test that github_token is forwarded to BaseGitHubManager."""
    repo_url = "https://github.com/test/repo.git"
    with patch("github.Github"):
        manager = CIResultsManager(repo_url=repo_url, github_token="explicit-token")
        assert manager.github_token == "explicit-token"
```

## DATA

No changes to return types. `CIResultsManager` gains one optional parameter.
`BaseGitHubManager` already handles the `github_token` parameter (verified at line 136).
