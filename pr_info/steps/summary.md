# Issue #197 — Fix malformed diff output from `edit_file`

## Problem

`mcp__mcp-workspace__edit_file` returns a malformed unified diff string. The
file edits apply correctly; only the returned diff text is wrong.

**Two intertwined defects, both inside `_create_diff` in
`src/mcp_workspace/file_tools/edit_file.py`:**

1. **Headers lack newlines.** `_create_diff` passes `lineterm=""` to
   `difflib.unified_diff`. difflib only appends `lineterm` to its synthetic
   header lines (`---`, `+++`, `@@`); content lines come from
   `splitlines(keepends=True)` and already carry their own newlines. The empty
   `lineterm` strips header terminators, so the three header lines and the
   first content line get concatenated.

2. **Paths are absolute and double-slashed.** `_create_diff` is called with
   `str(abs_path)`. On POSIX this is `/Users/.../file.txt`, which then gets
   prefixed `a/` → `a//Users/.../file.txt`. Git convention is repo-relative
   paths with forward slashes.

Both defects share a single root cause — the `_create_diff` helper — so they
are addressed in one step / one commit per `planning_principles.md`
("Merge tiny or intertwined steps").

## Fix overview (KISS)

Two narrow changes inside `_create_diff` plus updates to its two call
sites — total ~4 source lines touched.

| Change | Why |
|---|---|
| Drop `lineterm=""` (use difflib default `"\n"`) | Restores header newlines. |
| `filename = filename.replace("\\", "/")` inside helper | Forward slashes on all OSes (git convention). |
| Two call sites (empty-old-string prepend, normal-replace) pass `file_path` (relative) instead of `str(abs_path)` | Eliminates `a//...` and matches git-style output. The position-aware already-applied branch returns a literal string and does not call `_create_diff`. |

## Architectural / design changes

**None of significance.** The public API of `edit_file` is unchanged. The
private `_create_diff` helper keeps the same signature (`original`, `modified`,
`filename`) — only its internals change and what callers pass for `filename`.

Behavioral notes:

- The `project_dir=None` branch (direct Python callers only — not reachable
  via MCP per `server.py` which raises `ValueError` when `_project_dir` is
  unset) now receives whatever path the caller provided. If a test passes an
  absolute path it will still appear in the diff, but without the doubled
  slash (because `a/` + path no longer combines into `a//` once we stop
  forcing absolute paths via `abs_path`).
- No new modules, no new dependencies, no signature changes on public
  functions.

## Files modified

| File | Change |
|---|---|
| `src/mcp_workspace/file_tools/edit_file.py` | `_create_diff` internals + 2 call sites |
| `tests/file_tools/test_edit_file.py` | +2 regression tests (one parametrized over 2 cases) |

No files created, no files deleted, no folders restructured.

## Implementation steps

A single step, one commit, TDD ordering (failing tests first, then the
helper + call-site changes).

- **[Step 1](step_1.md)** — Fix `_create_diff`: drop `lineterm=""`, normalize
  backslashes to forward slashes, and switch the two call sites (empty-old-
  string prepend and normal-replace) to pass the relative `file_path`. Adds
  two regression tests (one parametrized over a flat filename and a
  Windows-style backslash relative path).

## Validation

After the step:

- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args: ["-n", "auto"]`
- `mcp__mcp-tools-py__run_mypy_check`

All three must pass before the commit.
