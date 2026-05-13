# Step 1 — Allow `--numstat` for `git show`

## Goal

Add `"--numstat"` to `SHOW_ALLOWED_FLAGS` for symmetry with `--stat` / `--shortstat` (already allowed for `show`) and with `--numstat` (already in `DIFF_ALLOWED_FLAGS`). Foundational change so the Step 3 tests for `git show --numstat` will not be blocked by validation.

## WHERE

- `src/mcp_workspace/git_operations/arg_validation.py` — edit `SHOW_ALLOWED_FLAGS` frozenset.
- `tests/git_operations/test_arg_validation.py` — add one test under an existing allowed-flags class for show (or add a small class if there isn't one).

## WHAT

No function signatures change. Frozenset gets one new member:

```python
SHOW_ALLOWED_FLAGS: frozenset[str] = frozenset(
    {
        ...
        "--stat",
        "--shortstat",
        "--numstat",     # <-- new
        "--name-only",
        ...
    }
)
```

## HOW

- Pure additive change to the existing allowlist; no imports, no decorators.
- `validate_args("show", ["--numstat"])` will now silently pass.

## ALGORITHM

N/A — single literal added to a frozenset.

## DATA

- Type: `frozenset[str]`
- Value: union of existing members + `"--numstat"`.

## Tests to write (TDD)

In `tests/git_operations/test_arg_validation.py`, add:

```python
class TestValidateArgsShowAllowed:
    """Allowed show flags pass through silently."""

    def test_numstat(self) -> None:
        validate_args("show", ["--numstat"])
```

(If a `TestValidateArgsShowAllowed` class already exists, append the test there. Inspect the file before deciding.)

Write the test first, see it fail, then edit `SHOW_ALLOWED_FLAGS` to make it pass.

## Verification

Run all three MCP checks after the change:

- `mcp__tools-py__run_pytest_check` (with `-n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"`)
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`

All must pass before commit.

## Commit

One commit: tests + allowlist change.

## LLM prompt

> Implement Step 1 as specified in `pr_info/steps/step_1.md`. Use `pr_info/steps/summary.md` as context for the overall fix. Follow TDD: write the failing test first, then add `"--numstat"` to `SHOW_ALLOWED_FLAGS` in `src/mcp_workspace/git_operations/arg_validation.py`. Run all three MCP code-quality checks (pytest with the recommended exclusion markers, pylint, mypy) and ensure they pass before producing exactly one commit. Use only MCP tools for file and check operations as required by `.claude/CLAUDE.md`.
