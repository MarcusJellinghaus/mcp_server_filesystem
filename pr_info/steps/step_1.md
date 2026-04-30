# Step 1 — Switch `search_files` glob matching to `pathspec` gitwildmatch

> **Context:** see `pr_info/steps/summary.md` for the architectural overview, behavior table, and rationale. This step is the entire fix.

## LLM Prompt

> Implement the change described in `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`).
>
> Replace `fnmatch.fnmatch`-based glob matching in `src/mcp_workspace/file_tools/search.py` with `pathspec.PathSpec.from_lines("gitwildmatch", ...)`. Normalize candidate paths from `\` to `/` *inside* `search_files` only, and on Windows lowercase both the pattern and candidates to preserve current case-insensitive behavior. Update the `search_files` docstring to a minimal example list. Add the 5 new tests listed below to `tests/file_tools/test_search.py`. Do **not** modify `_discover_files`, `list_directory`, or any other file. Use TDD: write the new tests first (they will fail under `fnmatch`), then make the implementation change so all tests pass. After the change, run `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check` (with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`), and `mcp__tools-py__run_mypy_check`. All three must pass before committing.

## WHERE

| Path | Action |
|---|---|
| `src/mcp_workspace/file_tools/search.py` | Modify (swap engine, add normalization, update docstring) |
| `tests/file_tools/test_search.py` | Modify (add 5 tests in `TestSearchFilesGlobOnly`) |

No new files, no new modules, no new directories.

## WHAT

### `search_files` — public signature unchanged

```python
def search_files(
    project_dir: Path,
    glob: Optional[str] = None,
    pattern: Optional[str] = None,
    context_lines: int = 0,
    max_results: int = 50,
    max_result_lines: int = 200,
) -> Dict[str, Any]: ...
```

Internals change; signature, return shape, and exceptions stay identical.

### Imports in `search.py`

- **Remove:** `import fnmatch`
- **Add:** `import sys`
- **Add:** `from pathspec import PathSpec`

### Docstring (minimal form, per decision #11)

Replace the `glob` arg description with a short note plus three examples:

```
glob: Glob pattern (gitignore semantics). Examples:
    ``*.py`` (any .py at any depth), ``tests/**/test_*.py``,
    ``/README.md`` (root only).
```

## HOW

- The change is fully contained inside the `if glob is not None:` branch of `search_files`.
- No new helper at module scope; a small inline `_norm` function is fine.
- `search_reference_files` is auto-fixed via the shared util — no separate edit.
- Public API (`__all__`, function signatures) is unchanged.

## ALGORITHM (core logic, ~6 lines)

```text
if glob is not None:
    norm_glob = glob.lower() if win32 else glob
    spec = PathSpec.from_lines("gitwildmatch", [norm_glob])
    def _norm(p): return (p.replace("\\", "/")).lower() if win32 else p.replace("\\", "/")
    matched = [f for f in all_files if spec.match_file(_norm(f))]
else:
    matched = all_files
```

Output paths in `matched` remain the original platform-native strings from `list_files` — only the value passed to `spec.match_file` is normalized.

## DATA

Return value shape is unchanged:

- File-search mode: `{"mode": "file_search", "files": List[str], "total_files": int, "truncated": bool}`
- Content-search mode: `{"mode": "content_search", "details": [...], "total_matches": int, "truncated": bool, ...}`

## Tests to Add (in `tests/file_tools/test_search.py`, class `TestSearchFilesGlobOnly`)

All five are required by the issue's "Test additions" section. Each must *prove* the new contract.

1. **`test_double_star_matches_root_file`** — the original bug.
   - Create `foo.bat` at project root.
   - Assert `search_files(project_dir, glob="**/foo.bat")` returns it.

2. **`test_bare_pattern_matches_at_any_depth`**
   - Create `a.py` at root and `sub/b.py` nested.
   - Assert `search_files(project_dir, glob="*.py")` returns both.

3. **`test_leading_slash_anchors_to_root`**
   - Create `foo.py` at root and `sub/foo.py` nested.
   - Assert `search_files(project_dir, glob="/foo.py")` returns only the root one.

4. **`test_star_does_not_cross_path_separator`**
   - Create `a/bfoo.py`.
   - Assert `search_files(project_dir, glob="*foo.py")` does **not** match it.

5. **`test_windows_case_insensitive_match_preserved`** — gated on `sys.platform == "win32"`.
   - Create `readme.md` at project root.
   - Assert `search_files(project_dir, glob="README.md")` returns it on Windows.
   - Use `pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")`.

### TDD Sequence

1. Add the 5 tests above to the existing `TestSearchFilesGlobOnly` class. Confirm they fail under the current `fnmatch` implementation (mentally — don't commit a failing state).
2. Apply the source change to `search.py` (engine swap + normalization + docstring).
3. Run all three quality checks; iterate until clean.
4. Single commit: tests + implementation + passing checks.

## Verification Checklist (before commit)

- [ ] `mcp__tools-py__run_pylint_check` — pass
- [ ] `mcp__tools-py__run_pytest_check` (with the recommended exclusion markers and `-n auto`) — pass
- [ ] `mcp__tools-py__run_mypy_check` — pass
- [ ] `./tools/format_all.sh` run, formatting changes (if any) staged
- [ ] No edits outside `src/mcp_workspace/file_tools/search.py` and `tests/file_tools/test_search.py`
