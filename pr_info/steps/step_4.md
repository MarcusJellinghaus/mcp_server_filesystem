# Step 4: Move github_operations Tests from mcp_coder

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. This is step 4 of 5 for issue #104.
>
> **Task:** Copy all `github_operations` test files from the installed `mcp_coder` package into `tests/github_operations/` (including `tests/github_operations/issues/` subdirectory). Adjust imports and fixtures to use `mcp_workspace` paths. Integration tests use `@pytest.mark.github_integration` with skip-if-no-token. Register the `github_integration` marker in `pyproject.toml`.
>
> **Source:** The test files live alongside the installed mcp_coder package. Use `get_library_source` to read test modules, or check the mcp_coder repo structure for test file locations. Adjust all imports to reference `mcp_workspace.github_operations` instead of `mcp_coder.utils.github_operations`.

## WHERE

### New test files

```
tests/github_operations/
  __init__.py
  conftest.py                    ← fixtures using config.get_github_token(), config.get_test_repo_url()
  test_base_manager.py
  test_github_utils.py
  test_pr_manager.py
  test_labels_manager.py
  test_ci_results_manager.py
  issues/
    __init__.py
    conftest.py                  ← if exists in mcp_coder
    test_branch_manager.py
    test_branch_naming.py
    test_cache.py
    test_comments_mixin.py
    test_events_mixin.py
    test_labels_mixin.py
    test_manager.py
    test_types.py
```

Note: Exact test file names depend on what exists in mcp_coder — copy all that exist.

### Files to modify

- `pyproject.toml` — add `github_integration` marker

## WHAT

### Test import remap

| Old import | New import |
|-----------|------------|
| `from mcp_coder.utils.github_operations.X import ...` | `from mcp_workspace.github_operations.X import ...` |
| `from mcp_coder.utils.github_operations.issues.X import ...` | `from mcp_workspace.github_operations.issues.X import ...` |
| `from mcp_coder.utils.user_config import ...` | `from mcp_workspace.config import ...` |

### Test fixture updates

The `conftest.py` fixtures that provide GitHub tokens and test repo URLs should use:
```python
from mcp_workspace.config import get_github_token, get_test_repo_url
```

Integration tests should be marked:
```python
@pytest.mark.github_integration
```

And should skip when no token is available:
```python
pytestmark = pytest.mark.github_integration

@pytest.fixture
def github_token():
    token = get_github_token()
    if not token:
        pytest.skip("GITHUB_TOKEN not configured")
    return token
```

### pyproject.toml marker registration

```toml
markers = [
    "git_integration: File system git operations (repos, commits)",
    "github_integration: GitHub API access (requires GITHUB_TOKEN)",
]
```

## HOW

### Pseudocode

```
for each test file in mcp_coder/tests/utils/github_operations/:
    content = read_source(file)
    content = apply_import_remap(content)
    content = update_fixture_references(content)
    save_file(tests/github_operations/..., content)

edit(pyproject.toml: add github_integration marker)
```

### Integration test handling

- Tests marked `@pytest.mark.github_integration` require `GITHUB_TOKEN` env var
- Tests auto-skip when no token is set (via fixture or `skipIf`)
- In CI, these run only in the `integration-tests` matrix entry (step 5)
- For local development, excluded by default via `-m "not github_integration"` pattern

## DATA

No new data structures. Test fixtures provide:
- `github_token: str` — from `config.get_github_token()`
- `test_repo_url: str` — from `config.get_test_repo_url()`

## Verification

```
pylint, mypy, pytest (unit tests only — exclude github_integration and git_integration)
Verify: all test files import from mcp_workspace, not mcp_coder
Verify: github_integration marker registered in pyproject.toml
```
