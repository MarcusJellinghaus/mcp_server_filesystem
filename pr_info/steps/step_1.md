# Step 1 — Add `check_ignore` to the argument-validation layer

## LLM Prompt

> Read `pr_info/steps/summary.md` for the overall task. Implement **only the changes described in this file** (`pr_info/steps/step_1.md`). Follow TDD: add the tests first, then make them pass with the minimum implementation. Use the MCP tools (`mcp__workspace__*` and `mcp__tools-py__run_*`) for all file edits and quality checks. After all edits, run `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and `mcp__tools-py__run_pytest_check` (use the fast-unit-test exclusion markers from `.claude/CLAUDE.md`). All three must pass. Produce exactly **one commit** containing the test additions and the implementation.

## Scope

Register `check_ignore` in the per-command allowlist and pathspec-supporting set, with no handler wiring yet. This step is independently green: it adds plumbing the dispatcher does not yet reach.

## WHERE

- **Source:** `src/mcp_workspace/git_operations/arg_validation.py`
- **Tests:** `tests/git_operations/test_arg_validation.py`

## WHAT

No new functions or signatures. Two module-level additions:

```python
CHECK_IGNORE_ALLOWED_FLAGS: frozenset[str] = frozenset(
    {"-v", "--verbose", "-n", "--non-matching", "--no-index"}
)
```

And the existing `_ALLOWLISTS` / `_SUPPORTS_PATHSPEC` registries are extended:

```python
_ALLOWLISTS["check_ignore"] = CHECK_IGNORE_ALLOWED_FLAGS
_SUPPORTS_PATHSPEC = frozenset({..., "check_ignore"})
```

(Edit the existing literal dict / frozenset in place — don't add assignments after the fact.)

## HOW (integration points)

- `CHECK_IGNORE_ALLOWED_FLAGS` placed alongside sibling constants (e.g. after `LS_REMOTE_ALLOWED_FLAGS`).
- `_ALLOWLISTS` gets a new entry `"check_ignore": CHECK_IGNORE_ALLOWED_FLAGS` — placement after `"ls_remote"` keeps the order matching the docstring.
- `_SUPPORTS_PATHSPEC` gains `"check_ignore"`.
- No changes to `validate_args` / `split_args_pathspec` / `validate_branch_has_read_flag` — they're allowlist-driven and pick the new command up automatically.

## ALGORITHM

No algorithmic logic — this is data registration only. `validate_args` already does:

```
if command not in _ALLOWLISTS: raise
for arg in args:
    if not arg.startswith("-"): continue
    if arg in allowlist or <prefix in allowlist> or <short-prefix in allowlist>: continue
    raise ValueError("not in the security allowlist")
```

## DATA

No runtime data shape change. Module-level constants only:

- `CHECK_IGNORE_ALLOWED_FLAGS: frozenset[str]` with exactly 5 entries.
- `_ALLOWLISTS: dict[str, frozenset[str]]` — gains one key.
- `_SUPPORTS_PATHSPEC: frozenset[str]` — gains one member.

## Tests to Add (TDD — write these first)

In `tests/git_operations/test_arg_validation.py`, add a new class:

```python
class TestValidateArgsCheckIgnoreAllowed:
    def test_verbose_short(self) -> None:
        validate_args("check_ignore", ["-v"])

    def test_verbose_long(self) -> None:
        validate_args("check_ignore", ["--verbose"])

    def test_non_matching_short(self) -> None:
        validate_args("check_ignore", ["-n"])

    def test_non_matching_long(self) -> None:
        validate_args("check_ignore", ["--non-matching"])

    def test_no_index(self) -> None:
        validate_args("check_ignore", ["--no-index"])

    def test_combined_verbose_non_matching(self) -> None:
        validate_args("check_ignore", ["-v", "-n"])


class TestValidateArgsCheckIgnoreRejected:
    def test_unknown_flag_raises(self) -> None:
        with pytest.raises(ValueError, match="not in the security allowlist"):
            validate_args("check_ignore", ["--stdin"])

    def test_quiet_rejected(self) -> None:
        with pytest.raises(ValueError, match="not in the security allowlist"):
            validate_args("check_ignore", ["-q"])


class TestSupportsPathspecCheckIgnore:
    def test_check_ignore_in_supports_pathspec(self) -> None:
        from mcp_workspace.git_operations.arg_validation import _SUPPORTS_PATHSPEC
        assert "check_ignore" in _SUPPORTS_PATHSPEC


class TestAllowlistsCheckIgnore:
    def test_check_ignore_in_allowlists(self) -> None:
        from mcp_workspace.git_operations.arg_validation import (
            _ALLOWLISTS,
            CHECK_IGNORE_ALLOWED_FLAGS,
        )
        assert "check_ignore" in _ALLOWLISTS
        assert _ALLOWLISTS["check_ignore"] == CHECK_IGNORE_ALLOWED_FLAGS
```

A direct membership assertion gives clearer failure messages than relying solely on `validate_args` accepting flags — if the allowlist key is missing or pointed at the wrong frozenset, this test pinpoints the cause immediately.

Confirm all new tests pass and no existing tests regress.

## Done When

- Both new test classes pass.
- All existing `test_arg_validation.py` cases still pass.
- `pylint`, `mypy --strict`, `pytest -n auto` clean.
- One commit, e.g. `git: add check_ignore allowlist and pathspec support`.
