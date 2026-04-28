# Step 1 — Fix `hostname_to_api_base_url()` for `*.ghe.com`

> See `pr_info/steps/summary.md` for the overall plan.

## LLM Prompt

> Read `pr_info/steps/summary.md` and then implement **Step 1** as described in `pr_info/steps/step_1.md`. Follow TDD: write the new tests first, run pytest to confirm they fail, then make the production change to make them pass. Run pylint, mypy, and pytest after every edit until all three pass. Commit with a single descriptive message — do not commit until all checks are green.

## WHERE

| Action | File | Symbol |
|---|---|---|
| Modify | `src/mcp_workspace/utils/repo_identifier.py` | `hostname_to_api_base_url()` |
| Modify | `tests/utils/test_repo_identifier.py` | `TestHostnameToApiBaseUrl` (extend) |

## WHAT

Same signature, extended dispatch:

```python
def hostname_to_api_base_url(hostname: str) -> str: ...
```

## HOW

- No new imports.
- No call-site changes — `RepoIdentifier.api_base_url` is a thin wrapper around this function and propagates the fix automatically.
- The two existing call paths (`base_manager.py:101` direct + `RepoIdentifier.api_base_url` property) need no edits.
- Update the docstring to mention the three product hostname patterns.

## ALGORITHM

```
h = hostname.lower()
if h == "github.com":           return "https://api.github.com"
if h.endswith(".ghe.com"):      return f"https://api.{h}"
return f"https://{hostname}/api/v3"   # original casing preserved for GHES
```

## DATA

Returns `str`. Three cases:

| Input | Output |
|---|---|
| `"github.com"` | `"https://api.github.com"` |
| `"GitHub.com"` | `"https://api.github.com"` (lowercased) |
| `"tenant.ghe.com"` | `"https://api.tenant.ghe.com"` |
| `"Foo.GHE.com"` | `"https://api.foo.ghe.com"` (lowercased) |
| `"ghe.corp.com"` | `"https://ghe.corp.com/api/v3"` (GHES, original casing) |
| `"ghe.com"` (bare) | `"https://ghe.com/api/v3"` (intentional fall-through) |

## Tests to Add (TDD — write first)

In `tests/utils/test_repo_identifier.py`, extend `TestHostnameToApiBaseUrl`:

1. `test_ghe_cloud_subdomain` — `tenant.ghe.com` → `https://api.tenant.ghe.com`
2. `test_ghe_cloud_mixed_case` — `Foo.GHE.com` → `https://api.foo.ghe.com`

Existing tests must continue to pass (github.com, ghe.corp.com, github.example.org).

## Quality Gates

- `mcp__tools-py__run_pytest_check` (with the standard `-n auto -m "not ..."` exclusion pattern)
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`

All three must pass before commit.

## Commit Message Suggestion

`Fix hostname_to_api_base_url() for *.ghe.com (GHE Cloud)`
