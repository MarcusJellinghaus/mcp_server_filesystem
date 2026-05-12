# Step 1 — Fix header newlines in `_create_diff`

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`).
> Implement Step 1 only. Follow TDD: add the regression test first, confirm
> it fails against the current code, then apply the one-line source fix and
> confirm the test passes. Run `mcp__tools-py__run_pylint_check`,
> `mcp__tools-py__run_pytest_check` (with the fast-unit-test marker exclusion
> from `.claude/CLAUDE.md`), and `mcp__tools-py__run_mypy_check`. All must
> pass before committing. Commit message:
> `fix(edit_file): restore newlines on unified-diff header lines`.

## WHERE

- **Modify:** `src/mcp_workspace/file_tools/edit_file.py` — function `_create_diff`.
- **Modify:** `tests/file_tools/test_edit_file.py` — add one new test method to `TestEditFile`.

## WHAT

### Test (write first)

```python
def test_diff_headers_have_newlines(self) -> None:
    """Unified diff header lines and hunk marker are newline-terminated."""
```

Assertion content: after a single-line edit, the returned diff, when split on
`"\n"`, contains at least four non-empty lines and the first three are the
`--- a/...`, `+++ b/...`, and `@@ ... @@` rows respectively. Confirms headers
are not concatenated into one run-on line.

### Source change

Inside `_create_diff`, remove the `lineterm=""` keyword argument from the
`difflib.unified_diff(...)` call so the default `"\n"` applies.

## HOW

- No imports change.
- No signature change on `_create_diff` or `edit_file`.
- No call-site change.
- difflib's default `lineterm="\n"` is appended only to its synthetic header
  lines (`---`, `+++`, `@@`); content lines already carry their own newlines
  from `splitlines(keepends=True)`, so no duplication occurs.

## ALGORITHM

```text
_create_diff(original, modified, filename):
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    return "".join(difflib.unified_diff(
        original_lines, modified_lines,
        fromfile=f"a/{filename}", tofile=f"b/{filename}"))   # lineterm omitted
```

## DATA

- `_create_diff` return type unchanged: `str` (the unified diff).
- The returned string now contains correctly newline-terminated header rows.
- No new data structures.

## Acceptance

- New test `test_diff_headers_have_newlines` passes.
- All pre-existing tests in `tests/file_tools/test_edit_file.py` still pass
  (they only check substring presence, which is unaffected).
- pylint, pytest, mypy all green.
- Exactly one commit.
