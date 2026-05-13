# Step 2 — Implement `git_check_ignore` handler and wire it into the dispatcher

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, and confirm Step 1 (`pr_info/steps/step_1.md`) is already merged (allowlist + `_SUPPORTS_PATHSPEC` entry exist for `check_ignore`). Implement **only the changes described in this file** (`pr_info/steps/step_2.md`). Follow TDD: add the integration tests first, then implement the handler + dispatcher wiring + docstring updates. Use the MCP tools (`mcp__workspace__*` and `mcp__tools-py__run_*`) for all file edits and quality checks. After all edits, run `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and `mcp__tools-py__run_pytest_check` (with the fast-unit-test exclusion markers AND `markers=["git_integration"]` separately, since the new tests are git-integration). All three must pass. Produce exactly **one commit** containing tests + implementation + docstring updates.

## Scope

End-to-end wiring of the new subcommand:

1. New `git_check_ignore` handler in `read_operations.py`.
2. Dispatcher registration in `git()`.
3. `_DEFAULT_MAX_LINES` entry.
4. Module docstring bump "11" → "12".
5. `server.py` MCP tool docstring update.
6. Six integration tests.

## WHERE

- **Source:** `src/mcp_workspace/git_operations/read_operations.py`
- **Source:** `src/mcp_workspace/server.py` (docstring only)
- **Tests:** `tests/git_operations/test_read_operations.py`

## WHAT

### New function signature

```python
def git_check_ignore(
    project_dir: Path,
    args: Optional[list[str]] = None,
    pathspec: Optional[list[str]] = None,
    max_lines: int = 50,
) -> str:
    """Run ``git check-ignore`` with validated arguments.

    Reports which of the given paths are excluded by gitignore rules.

    Note: With ``--no-index``, tracked files are still checked against
    ignore rules (without it, tracked files always report as "not ignored").

    Args:
        project_dir: Path to the git repository.
        args: Optional CLI flags (validated against allowlist).
        pathspec: File paths to test (required — must be non-empty).
        max_lines: Maximum output lines before truncation.

    Returns:
        Newline-separated matching paths (or rule sources when ``-v``),
        or ``"No paths are ignored."`` when none match.

    Raises:
        ValueError: If ``pathspec`` is empty/None, or any flag in
            ``args`` is not in the allowlist.
    """
```

### Dispatcher addition

In the `handlers` dict inside `git()`:

```python
"check_ignore": lambda: git_check_ignore(
    project_dir, safe_args, pathspec, resolved_max_lines
),
```

### `_DEFAULT_MAX_LINES` entry

```python
_DEFAULT_MAX_LINES: dict[str, int] = {
    "log": 50,
    "diff": 100,
    "status": 200,
    "check_ignore": 50,
}
```

### Module docstring bump

`read_operations.py` line ~5:
- `"... routes to all 11 supported sub-commands."` → `"... routes to all 12 supported sub-commands."`

### `server.py` MCP tool docstring

In `server.py:430-457`, extend the `command:` line of the `git()` tool docstring:

```
command: Git subcommand (log, diff, status, merge_base, fetch,
    show, branch, rev_parse, ls_tree, ls_files, ls_remote, check_ignore).
```

Leave the `max_lines` line unchanged (`"others=100"` — small inaccuracy acceptable per issue Decision #9).

## HOW (integration points)

- Import `Path`, `Optional`, `GitCommandError`, `safe_repo_context`, `truncate_output`, `validate_args`, `split_args_pathspec` — all already imported at top of `read_operations.py`.
- Place `git_check_ignore` after `git_branch` and before the `--- dispatcher ---` divider comment (alphabetical-ish; grouped with other handlers).
- **Do NOT** apply `_SAFETY_FLAGS` (check-ignore doesn't run diff/textconv).
- **Do NOT** use `_run_simple_command` (no exit-code-1 path).
- **Do NOT** add `check_ignore` to `_SUPPORTS_SEARCH` / `_SUPPORTS_COMPACT` / `_SUPPORTS_CONTEXT` — soft-warning behaviour from the dispatcher handles unsupported params automatically.
- **Do NOT** export from `git_operations/__init__.py` — tests import directly from `read_operations` (matches sibling convention; see summary).

## ALGORITHM

```
if not pathspec:
    raise ValueError("git check_ignore requires at least one path in 'pathspec'")
safe_args, pathspec = split_args_pathspec("check_ignore", args or [], pathspec)
validate_args("check_ignore", safe_args)
cmd_args = safe_args + ["--"] + pathspec
with safe_repo_context(project_dir) as repo:
    try:
        output = repo.git.check_ignore(*cmd_args)
    except GitCommandError as exc:
        if exc.status == 1:
            return "No paths are ignored."
        raise
return truncate_output(output, max_lines) if output else "No paths are ignored."
```

(The trailing `if output` branch handles the edge case where git produces empty stdout with exit 0 — unlikely but defensive.)

## DATA

| Input | Type |
|-------|------|
| `project_dir` | `Path` |
| `args` | `Optional[list[str]]` |
| `pathspec` | `Optional[list[str]]` (must be non-empty when present) |
| `max_lines` | `int` (default `50`) |

| Output scenario | Return value |
|-----------------|--------------|
| One or more paths matched, no `-v` | `"foo.txt\nbar.txt"` |
| Matched with `-v` | `".gitignore:5:*.txt\tfoo.txt"` |
| `-v -n` mixed | `".gitignore:5:*.txt\tfoo.txt\n::\tbar.txt"` |
| No matches | `"No paths are ignored."` |
| Empty `pathspec` | `raise ValueError(...)` |
| Disallowed flag | `raise ValueError("not in the security allowlist...")` |

## Tests to Add (TDD — write these first)

In `tests/git_operations/test_read_operations.py`:

1. Add `git_check_ignore` to the import block:

```python
from mcp_workspace.git_operations.read_operations import (
    _run_simple_command,
    git,
    git_branch,
    git_check_ignore,
    git_diff,
    git_log,
    git_merge_base,
    git_show,
    git_status,
)
```

2. Add the test class:

```python
@pytest.mark.git_integration
class TestGitCheckIgnore:
    """Tests for git_check_ignore()."""

    def _setup_ignored(self, project_dir: Path, repo: Repo) -> None:
        (project_dir / ".gitignore").write_text("*.txt\n")
        repo.index.add([".gitignore"])
        repo.index.commit("Add gitignore")

    def test_ignored_path_returns_path(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        self._setup_ignored(project_dir, repo)
        result = git_check_ignore(project_dir, pathspec=["foo.txt"])
        assert "foo.txt" in result

    def test_ignored_path_verbose_returns_rule_source(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        self._setup_ignored(project_dir, repo)
        result = git_check_ignore(project_dir, args=["-v"], pathspec=["foo.txt"])
        assert ".gitignore" in result
        assert "*.txt" in result
        assert "foo.txt" in result

    def test_verbose_non_matching_mixed_output(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        self._setup_ignored(project_dir, repo)
        result = git_check_ignore(
            project_dir, args=["-v", "-n"], pathspec=["foo.txt", "bar.md"]
        )
        assert "foo.txt" in result
        assert "bar.md" in result

    def test_none_ignored_returns_message(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        result = git_check_ignore(project_dir, pathspec=["bar.md"])
        assert result == "No paths are ignored."

    def test_empty_pathspec_raises(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with pytest.raises(ValueError, match="'pathspec'"):
            git_check_ignore(project_dir, pathspec=[])

    def test_none_pathspec_raises(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with pytest.raises(ValueError, match="'pathspec'"):
            git_check_ignore(project_dir, pathspec=None)

    def test_disallowed_flag_raises(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with pytest.raises(ValueError, match="not in the security allowlist"):
            git_check_ignore(project_dir, args=["--stdin"], pathspec=["foo.txt"])

    def test_dispatcher_routes_to_check_ignore(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        self._setup_ignored(project_dir, repo)
        result = git(
            command="check_ignore",
            project_dir=project_dir,
            pathspec=["foo.txt"],
        )
        assert "foo.txt" in result
```

(The last test confirms the dispatcher wiring is correct.)

## Done When

- All new tests pass (run with `markers=["git_integration"]`).
- `git_check_ignore` works via the unified `git()` dispatcher.
- `read_operations.py` module docstring says "12 supported sub-commands".
- `server.py` `git()` tool docstring includes `check_ignore` in the subcommand list.
- `pylint`, `mypy --strict`, fast-unit-test pytest, and `git_integration`-marker pytest all clean.
- One commit, e.g. `git: add check_ignore subcommand to read-only dispatcher`.
