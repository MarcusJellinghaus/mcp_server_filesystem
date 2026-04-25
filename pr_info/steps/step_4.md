# Step 4: Export from `__init__.py` and update vulture whitelist

**Ref:** See `pr_info/steps/summary.md` for full context (Issue #157).

## LLM Prompt

> Implement Step 4 of the verify_github plan (see `pr_info/steps/summary.md`).
> Export `verify_github` and `CheckResult` from `github_operations/__init__.py`.
> Add new public API symbols to `vulture_whitelist.py`.
> Run all quality checks before committing.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_workspace/github_operations/__init__.py` | Add imports and `__all__` entries |
| `vulture_whitelist.py` | Add new public API symbols |

## WHAT

### `__init__.py` changes

```python
from .verification import CheckResult, verify_github

__all__ = [
    # ... existing entries ...
    "CheckResult",
    "verify_github",
]
```

### `vulture_whitelist.py` additions

Under the `# GitHub Operations` section:

```python
# Verification API (verify_github)
_.verify_github
_.CheckResult
# Note: get_default_branch is called by verify_github() — only add if vulture flags it
```

## HOW

- Add import line for `verification` module alongside existing imports in `__init__.py`
- Add to `__all__` list in alphabetical position
- Add vulture whitelist entries for symbols that are public API but not called within `mcp_workspace` itself

## TESTS

No new tests — this step is wiring only. Existing tests from Steps 1–3 validate the functionality. Run full test suite to confirm nothing broke.

## COMMIT

```
chore: export verify_github and update whitelist (#157)
```
