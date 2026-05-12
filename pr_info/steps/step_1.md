# Step 1 — Fix malformed unified diff in `_create_diff`

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`).
> Implement Step 1 (the only step). Follow TDD: add the two regression tests
> first, confirm they fail against the current code, then apply the source
> changes (drop `lineterm=""`, add backslash-to-forward-slash normalization,
> and update the three `_create_diff` call sites to pass the relative
> `file_path` instead of `str(abs_path)`), then confirm the tests pass. Run
> `mcp__mcp-tools-py__run_pylint_check`,
> `mcp__mcp-tools-py__run_pytest_check` with
> `extra_args: ["-n", "auto"]`, and
> `mcp__mcp-tools-py__run_mypy_check`. All must pass before committing.
> Commit message:
> `fix(edit_file): produce well-formed unified diff (newline-terminated headers, forward-slash relative paths)`.

## WHERE

- **Modify:** `src/mcp_workspace/file_tools/edit_file.py`
  - Function `_create_diff` — drop `lineterm=""` from the
    `difflib.unified_diff(...)` call and add a forward-slash normalization
    for the `filename` parameter.
  - Function `edit_file` — the three `_create_diff` call sites (the
    empty-old-string return, the position-aware return, and the
    normal-replace return). Each currently passes `str(abs_path)`; switch to
    passing the relative `file_path` (or `file_path` as-given when
    `project_dir` is `None`).
- **Modify:** `tests/file_tools/test_edit_file.py` — add two new tests to
  `TestEditFile` (one of them parametrized).

## WHAT

### Tests (write first)

**Test A — header newlines:**

```python
def test_diff_headers_have_newlines(self) -> None:
    """Header lines and hunk marker are separated by `\\n`, not run together."""
```

After a small edit via the public `edit_file` API, assert the returned diff
contains the substrings `"\n+++ "` and `"\n@@ "`. This is behavior-focused
(no `splitlines` parsing): it directly proves the `---`, `+++`, and `@@`
headers are newline-separated from one another and from the first content
line.

**Test B — forward-slash relative paths (parametrized):**

```python
@pytest.mark.parametrize(
    "file_path, expected_from, expected_to",
    [
        ("test_file.py", "--- a/test_file.py", "+++ b/test_file.py"),
        ("sub\\dir\\test_file.py", "--- a/sub/dir/test_file.py", "+++ b/sub/dir/test_file.py"),
    ],
)
def test_diff_uses_relative_forward_slash_path(
    self, file_path: str, expected_from: str, expected_to: str
) -> None:
    """Diff header paths are relative and use forward slashes (no `a//...`, no backslashes)."""
```

For each case, set up a file at the corresponding relative location under
`self.project_dir`, invoke `edit_file` with `project_dir=self.project_dir`
and the parametrized `file_path`, and assert:

- the diff contains `expected_from` and `expected_to`,
- the diff does **not** contain the substring `"a//"`,
- no backslash appears inside the `---` / `+++` header lines.

The second case literally exercises the `.replace("\\", "/")` normalization.

### Source changes

1. Inside `_create_diff`, drop `lineterm=""` from the
   `difflib.unified_diff(...)` call so its default `"\n"` is used and the
   synthetic header lines are properly newline-terminated.
2. Inside `_create_diff`, add normalization as the first statement:
   ```python
   filename = filename.replace("\\", "/")
   ```
3. At each of the three `_create_diff` call sites inside `edit_file` (the
   empty-old-string return, the position-aware return, and the normal-replace
   return — identified by behavior, not line number), replace
   `str(abs_path)` with the function parameter `file_path` (relative when
   `project_dir` is set; passed through as-is otherwise).

## HOW

- No imports change.
- No signature change on `_create_diff` or `edit_file`.
- difflib's default `lineterm="\n"` is appended only to its synthetic header
  lines (`---`, `+++`, `@@`); content lines already carry their own newlines
  from `splitlines(keepends=True)`, so no duplication occurs.
- The `project_dir=None` branch (not reachable via MCP because
  `server.py:edit_file` raises `ValueError` when `_project_dir` is unset)
  uses the caller-supplied path verbatim — still better than the previous
  `a/` + absolute-path concatenation that produced `a//...`.

## ALGORITHM

```text
_create_diff(original, modified, filename):
    filename = filename.replace("\\", "/")       # NEW: git convention, all OSes
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    return "".join(difflib.unified_diff(
        original_lines, modified_lines,
        fromfile=f"a/{filename}", tofile=f"b/{filename}"))   # lineterm omitted

# In edit_file: three return sites become
return _create_diff(original_content, modified_content, file_path)
```

## DATA

- `_create_diff` return type unchanged: `str` (the unified diff).
- The returned string now has correctly newline-terminated header rows and
  repo-relative, forward-slash header paths (e.g. `--- a/sub/dir/file.py`).
- No new data structures.

## Acceptance

- New test `test_diff_headers_have_newlines` passes.
- Parametrized test `test_diff_uses_relative_forward_slash_path` passes for
  both cases.
- All pre-existing tests in `tests/file_tools/test_edit_file.py` still pass
  (the existing `test_basic_replacement` passes an absolute path and only
  checks `+`/`-` content substrings, which is unaffected).
- pylint, pytest (with `extra_args: ["-n", "auto"]`), mypy all green.
- Exactly one commit.

## Commit message

```
fix(edit_file): produce well-formed unified diff (newline-terminated headers, forward-slash relative paths)
```
