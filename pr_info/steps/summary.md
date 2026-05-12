# Issue #197 — Fix malformed diff output from `edit_file`

## Problem

`mcp__mcp-workspace__edit_file` returns a malformed unified diff string. The
file edits apply correctly; only the returned diff text is wrong.

**Two independent defects in `src/mcp_workspace/file_tools/edit_file.py`:**

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

## Fix overview (KISS)

Two narrow changes inside `_create_diff` plus updates to its three call
sites — total ~5 source lines touched.

| Change | Why |
|---|---|
| Drop `lineterm=""` (use difflib default `"\n"`) | Restores header newlines. |
| `filename = filename.replace("\\", "/")` inside helper | Forward slashes on all OSes (git convention). |
| Call sites pass `file_path` (relative) instead of `str(abs_path)` | Eliminates `a//...` and matches git-style output. |

## Architectural / design changes

**None of significance.** The public API of `edit_file` is unchanged. The
private `_create_diff` helper keeps the same signature (`original`, `modified`,
`filename`) — only its internals change and what callers pass for `filename`.

Behavioral notes:

- The `project_dir=None` branch (direct Python callers only — not reachable
  via MCP per `server.py` line ~417 which raises `ValueError`) now receives
  whatever path the caller provided. If a test passes an absolute path it will
  still appear in the diff, but without the doubled slash (because `a/` + path
  no longer combines into `a//` once we stop forcing absolute paths via
  `abs_path`).
- No new modules, no new dependencies, no signature changes on public
  functions.

## Files modified

| File | Change |
|---|---|
| `src/mcp_workspace/file_tools/edit_file.py` | `_create_diff` internals + 3 call sites |
| `tests/file_tools/test_edit_file.py` | +2 regression tests (one per defect) |

No files created, no files deleted, no folders restructured.

## Implementation steps

Each step is one commit, follows TDD (failing test first, then minimal fix),
and addresses exactly one of the two defects.

- **[Step 1](step_1.md)** — Fix header newlines (`lineterm`).
- **[Step 2](step_2.md)** — Fix relative + forward-slash path.

Steps are independent and could be reordered, but Step 1 is presented first
because it is the smaller, more localized change.

## Validation

After each step:

- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check` with the fast-unit-test marker exclusion
  per `.claude/CLAUDE.md`
- `mcp__tools-py__run_mypy_check`

All three must pass before the commit.
