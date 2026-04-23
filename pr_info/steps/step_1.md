# Step 1: Add Numeric Flag Support with Tests

**Reference:** See [summary.md](summary.md) for full context (Issue #133).

## Goal

Enable `validate_args()` to accept bare numeric flags (`-10`, `-3`, `-5`) for `log`, `show`, and `diff` commands, while continuing to reject them for all other commands.

## WHERE

- `tests/git_operations/test_arg_validation.py` — new test class
- `src/mcp_workspace/git_operations/arg_validation.py` — sentinel + detection logic

## WHAT

### Tests to add (new class `TestValidateArgsNumericFlags`)

```python
class TestValidateArgsNumericFlags:
    """Bare numeric flags like -10 are allowed for opted-in commands."""

    def test_log_numeric_flag(self) -> None:
        validate_args("log", ["--oneline", "-10"])

    def test_show_numeric_flag(self) -> None:
        validate_args("show", ["-3"])

    def test_diff_numeric_flag(self) -> None:
        validate_args("diff", ["-5"])

    def test_status_rejects_numeric_flag(self) -> None:
        with pytest.raises(ValueError, match="-10"):
            validate_args("status", ["-10"])

    def test_branch_rejects_numeric_flag(self) -> None:
        with pytest.raises(ValueError, match="-5"):
            validate_args("branch", ["-5"])

    def test_non_numeric_flag_still_rejected(self) -> None:
        with pytest.raises(ValueError, match="-abc"):
            validate_args("log", ["-abc"])
```

### Production code changes

1. Add `"-<int>"` to `LOG_ALLOWED_FLAGS`, `DIFF_ALLOWED_FLAGS`, `SHOW_ALLOWED_FLAGS`
2. Add numeric detection branch in `validate_args()` after the short-flag check

## HOW

### Integration points

- No new imports needed
- No changes to `read_operations.py` or the dispatcher
- Sentinel `"-<int>"` is just a string in existing frozensets

## ALGORITHM (detection logic in `validate_args`)

```
for arg in args:
    if not arg.startswith("-"): continue
    if arg in allowlist: continue
    if "=" in arg and prefix in allowlist: continue
    if len(arg) > 2 and short_prefix in allowlist: continue
    # NEW: bare numeric flag like -10
    if not arg.startswith("--") and arg[1:].isdigit() and "-<int>" in allowlist: continue
    raise ValueError(...)
```

## DATA

- No new return values or data structures
- `"-<int>"` is a sentinel string marker in existing `frozenset[str]`

## Commit

```
feat: support bare numeric flags (-10) in git log/show/diff

Add sentinel marker "-<int>" to log, show, and diff allowlists.
Detect bare numeric flags in validate_args() and allow them
when the command opts in via the sentinel.

Closes #133
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md, then implement step 1.

TDD approach: write the tests first in tests/git_operations/test_arg_validation.py,
verify they fail, then add the sentinel and detection logic in
src/mcp_workspace/git_operations/arg_validation.py.

Run all three code quality checks (pylint, pytest, mypy) after implementation.
```
