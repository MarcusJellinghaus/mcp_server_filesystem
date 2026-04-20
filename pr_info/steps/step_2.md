# Step 2: Add New Git Command Implementations

## Context
See [summary.md](./summary.md) for full context. This step adds the `_run_simple_command()` helper, `git_show()`, and `git_branch()` to `read_operations.py`.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.
Implement Step 2: add _run_simple_command() helper, git_show(), and git_branch() in read_operations.py, with tests.
Follow TDD — write tests first, then implementation. Run all three quality checks after.
```

## WHERE
- `src/mcp_workspace/git_operations/read_operations.py` — add functions
- `tests/git_operations/test_read_operations.py` — add tests

## WHAT

### `_run_simple_command()` — private helper
```python
def _run_simple_command(
    git_method: str,
    project_dir: Path,
    command: str,
    args: list[str],
    pathspec: Optional[list[str]],
    max_lines: int,
    no_output_message: str = "No output.",
    use_safety_flags: bool = True,
) -> str:
```
Used by: `git_status` (could be refactored later), `git_merge_base` (ditto), and the new simple commands (fetch, rev_parse, ls_tree, ls_files, ls_remote). For now, only the new commands use it — existing functions are left unchanged.

### `git_show()` — dedicated function
```python
def git_show(
    project_dir: Path,
    args: Optional[list[str]] = None,
    pathspec: Optional[list[str]] = None,
    search: Optional[str] = None,
    context: int = 3,
    max_lines: int = 100,
    compact: bool = True,
) -> str:
```

### `git_branch()` — dedicated function
```python
def git_branch(
    project_dir: Path,
    args: Optional[list[str]] = None,
    max_lines: int = 100,
) -> str:
```

## HOW
- `_run_simple_command` uses `_safe_repo_context`, `validate_args`, `_SAFETY_FLAGS`, `truncate_output` — all existing imports
- `git_show` reuses compact diff rendering from `git_diff` pattern; detects colon pattern to skip compact
- `git_branch` calls `validate_branch_has_read_flag` (from step 1) before executing
- Import `validate_branch_has_read_flag` from `.arg_validation`

## ALGORITHM (_run_simple_command)
```
1. validate_args(command, args)
2. cmd_args = (SAFETY_FLAGS if use_safety_flags else []) + args
3. if pathspec: cmd_args += ["--"] + pathspec
4. with _safe_repo_context: output = getattr(repo.git, git_method)(*cmd_args)
5. if not output: return no_output_message
6. return truncate_output(output, max_lines)
```

## ALGORITHM (git_show — compact detection)
```
1. validate_args("show", args)
2. has_colon = any(":" in a and not a.startswith("-") for a in args)
3. if compact and not has_colon: apply compact rendering (same as git_diff)
4. else: plain execution with SAFETY_FLAGS
5. if search: apply filter_diff_output
6. return truncate_output
```

## ALGORITHM (git_branch)
```
1. validate_args("branch", args)
2. validate_branch_has_read_flag(args)
3. cmd_args = args (no SAFETY_FLAGS — branch doesn't use ext-diff)
4. with _safe_repo_context: output = repo.git.branch(*cmd_args)
5. return truncate_output(output, max_lines) or "No branches found."
```

## DATA
- All functions return `str`
- `_run_simple_command` is generic: `git_method` is the GitPython method name (e.g. `"fetch"`, `"rev_parse"`, `"ls_tree"`)
- For `ls_tree`, `ls_files`: GitPython method names are `ls_tree`, `ls_files` (with underscore)
- For `ls_remote`: GitPython method name is `ls_remote`

## TESTS (write first)
In `test_read_operations.py`, add:

### `TestRunSimpleCommand` (unit tests with mocked repo)
- `test_validates_args` — verify validate_args is called
- `test_appends_pathspec` — verify `--` + pathspec appended
- `test_truncates_output` — verify max_lines applied
- `test_no_output_message` — verify custom message on empty output
- `test_includes_safety_flags` — verify `--no-ext-diff`, `--no-textconv` injected when `use_safety_flags=True`
- `test_no_safety_flags` — verify safety flags omitted when `use_safety_flags=False`

### `TestGitShow` (integration, `@pytest.mark.git_integration`)
- `test_show_head_commit` — shows HEAD commit info
- `test_show_compact_default` — compact rendering applied
- `test_show_colon_skips_compact` — `HEAD:README.md` skips compact
- `test_show_search_filters` — search parameter works
- `test_show_rejected_flag_raises` — disallowed flag raises ValueError

### `TestGitBranch` (integration, `@pytest.mark.git_integration`)
- `test_branch_list` — `--list` returns branches
- `test_branch_all` — `-a` works
- `test_branch_show_current` — `--show-current` returns current branch name
- `test_branch_bare_rejected` — empty args raises ValueError
- `test_branch_no_read_flag_rejected` — args without read-only flag raises ValueError
- `test_branch_rejected_flag_raises` — disallowed flag raises ValueError
