# Issue #190 — `git`: support `check-ignore` subcommand

## Goal

Add `check_ignore` as the **12th** read-only subcommand of the unified `git` MCP tool so LLM callers can query gitignore rules directly (without falling back to `Bash`).

Example call shape:

```python
git(
    command="check_ignore",
    pathspec=[".mcp.linux.json", ".mcp.windows.json", ".mcp.macos.json"],
    args=["-v", "-n"],
)
```

## Architectural / Design Notes

- **No new modules, no new packages, no layering changes.** This is a feature addition along an existing seam.
- **Mirrors `git_merge_base` patterns.** A dedicated handler is required because `git check-ignore` uses tri-state exit codes (`0` = match, `1` = no match, `128` = fatal). GitPython raises `GitCommandError` on any non-zero status, so we explicitly catch `status == 1` and return a friendly message — exactly how `git_merge_base` handles `--is-ancestor`'s exit-1 semantics.
- **Cannot reuse `_run_simple_command`.** That helper has no exit-code-1 path. Adding the special-case to `_run_simple_command` for a single caller would be premature abstraction (rejected on KISS grounds).
- **No safety flags (`--no-ext-diff`, `--no-textconv`).** `check-ignore` does not invoke diff or textconv pipelines.
- **`--stdin`, `-q/--quiet`, `-z` are intentionally NOT supported.** MCP tools take structured parameters, exit-code-only modes are useless to LLM callers, and NUL-terminated output renders poorly as text.
- **Error message names the MCP parameter, not the CLI flag.** `"requires at least one path in 'pathspec'"` is more actionable than git's native `fatal: no path specified`.
- **`__init__.py` is NOT modified.** The issue says to export `git_check_ignore` "consistent with sibling handlers like `git_merge_base`", but the *actual* convention is that `git_log`, `git_diff`, `git_merge_base`, `git_show`, `git_status`, `git_branch` are **not** in `__init__.py` — tests import them directly from `read_operations`. We follow the *actual* convention. (Project-wide harmonisation, if desired, is a separate refactor.)

## Files Created / Modified

### Source (modified)
| File | Change |
|------|--------|
| `src/mcp_workspace/git_operations/arg_validation.py` | Add `CHECK_IGNORE_ALLOWED_FLAGS`; register in `_ALLOWLISTS` and `_SUPPORTS_PATHSPEC`. |
| `src/mcp_workspace/git_operations/read_operations.py` | Add `git_check_ignore` handler; register in dispatcher; add `_DEFAULT_MAX_LINES` entry; bump module docstring "11" → "12". |
| `src/mcp_workspace/server.py` | Extend `git()` tool docstring to list `check_ignore`. |

### Tests (modified)
| File | Change |
|------|--------|
| `tests/git_operations/test_arg_validation.py` | Add cases for `check_ignore` allowlist (allowed flags pass, disallowed reject). |
| `tests/git_operations/test_read_operations.py` | Add `TestGitCheckIgnore` class covering 6 scenarios. |

### Untouched (intentional)
| File | Reason |
|------|--------|
| `src/mcp_workspace/git_operations/__init__.py` | Sibling handlers (`git_merge_base`, `git_log`, etc.) are **not** currently exported. The issue's Decision #7 claims they are — verified against the codebase, they aren't. Following the *actual* convention; project-wide harmonisation is a separate refactor. |
| `tests/git_operations/test_init_exports.py` | Not modified — no `__all__` change. |

## Step Plan

| Step | Scope | Commit |
|------|-------|--------|
| 1 | Validation layer: allowlist + `_SUPPORTS_PATHSPEC` entry + arg-validation tests | one |
| 2 | Handler, dispatcher wiring, integration tests, MCP docstring updates | one |

Each step is independently green (tests pass, lint passes) without the next step.

## Acceptance Criteria

- `git(command="check_ignore", pathspec=[...], args=[...])` works end-to-end.
- All 6 documented scenarios in `tests/git_operations/test_read_operations.py::TestGitCheckIgnore` pass.
- `git(command="check_ignore", pathspec=[...])` with non-ignored paths returns `"No paths are ignored."` (not a raised exception).
- Empty/None `pathspec` raises `ValueError` naming the `pathspec` parameter.
- Disallowed flag (e.g. `--exec=evil`) raises the standard allowlist `ValueError`.
- `pylint`, `mypy --strict`, and `pytest -n auto` (with the standard exclusion markers) all pass.
