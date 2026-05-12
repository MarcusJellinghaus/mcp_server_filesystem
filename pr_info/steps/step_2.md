# Step 2 — Fix path in diff: relative + forward slashes

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`).
> Step 1 must already be merged. Implement Step 2 only. Follow TDD: add the
> regression test first, confirm it fails against the current code, then
> apply the source changes (one line added inside `_create_diff`, three
> call-site edits in `edit_file`) and confirm the test passes. Run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check` (with
> the fast-unit-test marker exclusion from `.claude/CLAUDE.md`), and
> `mcp__tools-py__run_mypy_check`. All must pass before committing. Commit
> message: `fix(edit_file): use relative forward-slash paths in diff output`.

## WHERE

- **Modify:** `src/mcp_workspace/file_tools/edit_file.py`
  - Function `_create_diff` (one line added).
  - Function `edit_file` — the three call sites of `_create_diff` (currently
    near lines 60, 81, 84 — the empty-old-string return, the position-aware
    return, and the normal-replace return).
- **Modify:** `tests/file_tools/test_edit_file.py` — add one new test method
  to `TestEditFile`.

## WHAT

### Test (write first)

```python
def test_diff_uses_relative_forward_slash_path(self) -> None:
    """Diff header paths are relative and use forward slashes (no `a//...`)."""
```

Assertion content: invoke `edit_file` with `project_dir=self.project_dir` and
`file_path="test_file.py"` (relative). Assert the returned diff contains
exactly `--- a/test_file.py` and `+++ b/test_file.py` on their own lines, and
does **not** contain the substring `a//` or any backslash inside the header
paths. Locks in both the relative-path and forward-slash requirements.

### Source changes

1. Inside `_create_diff`, add normalization as the first statement:
   ```python
   filename = filename.replace("\\", "/")
   ```
2. At each of the three call sites in `edit_file`, replace `str(abs_path)`
   with `file_path` (the function parameter — already relative when
   `project_dir` is set; passed through as-is otherwise per the issue's
   decision table).

## HOW

- No imports change.
- No signature change on `_create_diff` or `edit_file`.
- The `project_dir=None` branch — unreachable via MCP because
  `server.py:edit_file` raises `ValueError` when `_project_dir` is unset —
  uses the caller-supplied path verbatim. Direct callers (tests) that pass
  absolute paths will see those absolute paths in the diff, but without the
  doubled slash that the old `a/` + absolute-path concatenation produced.

## ALGORITHM

```text
_create_diff(original, modified, filename):
    filename = filename.replace("\\", "/")               # NEW: git convention
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    return "".join(difflib.unified_diff(
        original_lines, modified_lines,
        fromfile=f"a/{filename}", tofile=f"b/{filename}"))

# In edit_file: three return sites become
return _create_diff(original_content, modified_content, file_path)
```

## DATA

- `_create_diff` return type unchanged: `str`.
- Header rows now read `--- a/<relative-forward-slash-path>` and
  `+++ b/<relative-forward-slash-path>`.
- No new data structures.

## Acceptance

- New test `test_diff_uses_relative_forward_slash_path` passes.
- The Step 1 test `test_diff_headers_have_newlines` still passes.
- All pre-existing tests in `tests/file_tools/test_edit_file.py` still pass.
  The existing `test_basic_replacement` test (which passes an absolute
  `str(self.test_file)` and only checks `+`/`-` content substrings) is
  unaffected.
- pylint, pytest, mypy all green.
- Exactly one commit.
