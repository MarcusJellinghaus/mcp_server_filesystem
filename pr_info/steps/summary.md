# Issue #177 — Switch `search_files` glob matching to `pathspec` gitwildmatch

## Goal

Fix `search_files(glob=...)` so that standard glob semantics apply (notably `**/foo` matching at any depth, including the root). Replace `fnmatch.fnmatch` with the already-declared-but-unused `pathspec` library using its `gitwildmatch` pattern style — the same gitignore semantics already used elsewhere in the project.

## Architectural / Design Changes

This is a **localized bug fix**, not an architectural change.

- **No new dependency.** `pathspec>=0.12.1` is already declared in `pyproject.toml:25`. It was previously unused; this change activates it.
- **No new module, no new public function, no new layer.** The fix lives entirely inside `search_files` in `src/mcp_workspace/file_tools/search.py`.
- **No change to `_discover_files` or `list_directory`.** Path-separator normalization and case folding happen *inside* `search_files` only, so `list_directory` (which depends on `_discover_files`) is unaffected. Decision #12 in the issue.
- **`search_reference_files` is auto-fixed** because it shares the same `search_files` util — no separate code change required.
- **Engine alignment.** The project already uses gitignore semantics for `.gitignore` filtering (via `igittigitt`). Adopting `pathspec` gitwildmatch for user-facing glob patterns gives users one consistent mental model.

## Behavior Changes (User-Visible)

| Pattern | Before (`fnmatch`) | After (`pathspec` gitwildmatch) |
|---|---|---|
| `**/foo.py` | nothing if `foo.py` at root | matches `foo.py` at any depth (the bug) |
| `*.py` | only root `*.py` | every `.py` file at any depth |
| `foo.py` | only root `foo.py` | `foo.py` at any depth |
| `/foo.py` | matches nothing | only root `foo.py` |
| `*foo.py` | matches across `/` (e.g. `a/bfoo.py`) | matches within one segment only |
| `src/*.py` | direct children of `src/` only | direct children of `src/` only (unchanged) |
| `README.md` on Windows | case-insensitive | case-insensitive (preserved) |

The `pattern` (regex) parameter and all output formats are unchanged.

## Files Created / Modified

### Modified

| File | Change |
|---|---|
| `src/mcp_workspace/file_tools/search.py` | Replace `fnmatch.fnmatch` with `pathspec.PathSpec.from_lines("gitwildmatch", ...)`. Add internal `\` → `/` normalization and Windows case-folding. Update `search_files` docstring to a minimal example list. |
| `tests/file_tools/test_search.py` | Add 5 new tests in `TestSearchFilesGlobOnly` covering the new contract (see Step 1). |

### Created

None. No new files, no new directories.

### Not Modified

- `src/mcp_workspace/file_tools/directory_utils.py` — `_discover_files` stays untouched (per decision #12).
- `src/mcp_workspace/file_tools/__init__.py` — public surface unchanged.
- `src/mcp_workspace/server.py` and `src/mcp_workspace/server_reference_tools.py` — call sites unchanged.
- `pyproject.toml` — `pathspec` is already declared.

## Out of Scope (per Issue Decisions)

- Normalizing output path separators (output stays platform-native).
- Migrating `directory_utils.py` from `igittigitt` to `pathspec`.
- Any change to the `pattern` (regex) parameter.
- Any change to `list_directory`.

## Implementation Plan

This is a single atomic change — one source file + one test file — so it produces one commit.

- **Step 1** (`step_1.md`): Replace `fnmatch` with `pathspec` gitwildmatch in `search_files`, add the 5 contract tests, update the docstring. All checks pass.
