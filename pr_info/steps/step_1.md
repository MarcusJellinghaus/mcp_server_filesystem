# Step 1: Add Allowlists for 7 New Git Commands

## Context
See [summary.md](./summary.md) for full context. This step adds argument validation allowlists for the 7 new git commands.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.
Implement Step 1: add argument validation allowlists for 7 new git commands in arg_validation.py, with tests.
Follow TDD — write tests first, then implementation. Run all three quality checks after.
```

## WHERE
- `src/mcp_workspace/git_operations/arg_validation.py` — add allowlists
- `tests/git_operations/test_arg_validation.py` — add tests

## WHAT

### New constants in `arg_validation.py`:

```python
FETCH_ALLOWED_FLAGS: frozenset[str]
# --all, --prune, --tags, --no-tags, --depth, --shallow-since,
# --shallow-exclude, --force, -f, --verbose, -v, --quiet, -q,
# --dry-run, -n

SHOW_ALLOWED_FLAGS: frozenset[str]
# --format, --pretty, --abbrev-commit, --no-abbrev-commit, --date,
# --stat, --shortstat, --name-only, --name-status, --no-patch,
# --patch, -p, --unified, -U, --diff-filter, --no-ext-diff,
# --no-textconv, --oneline, -M, -C, --find-renames, --find-copies,
# --color-words, --word-diff

BRANCH_ALLOWED_FLAGS: frozenset[str]
# --list, -a, -r, --contains, --merged, --no-merged, --sort,
# -v, --show-current, --no-color

REV_PARSE_ALLOWED_FLAGS: frozenset[str]
# --abbrev-ref, --short, --verify, --symbolic, --symbolic-full-name,
# --show-toplevel, --show-cdup, --git-dir, --is-inside-work-tree,
# --is-bare-repository, --show-prefix, --show-superproject-working-tree

LS_TREE_ALLOWED_FLAGS: frozenset[str]
# -r, -t, -d, --name-only, --name-status, --long, -l,
# --abbrev, --full-name, --full-tree

LS_FILES_ALLOWED_FLAGS: frozenset[str]
# --cached, -c, --deleted, -d, --modified, -m, --others, -o,
# --ignored, -i, --stage, -s, --unmerged, -u, --exclude,
# --exclude-standard, --error-unmatch, --full-name, --abbrev

LS_REMOTE_ALLOWED_FLAGS: frozenset[str]
# --heads, --tags, --refs, --quiet, -q, --sort, --get-url
```

### Register in `_ALLOWLISTS`:
```python
_ALLOWLISTS: dict[str, frozenset[str]] = {
    "log": LOG_ALLOWED_FLAGS,
    "diff": DIFF_ALLOWED_FLAGS,
    "status": STATUS_ALLOWED_FLAGS,
    "merge_base": MERGE_BASE_ALLOWED_FLAGS,
    "fetch": FETCH_ALLOWED_FLAGS,
    "show": SHOW_ALLOWED_FLAGS,
    "branch": BRANCH_ALLOWED_FLAGS,
    "rev_parse": REV_PARSE_ALLOWED_FLAGS,
    "ls_tree": LS_TREE_ALLOWED_FLAGS,
    "ls_files": LS_FILES_ALLOWED_FLAGS,
    "ls_remote": LS_REMOTE_ALLOWED_FLAGS,
}
```

### New validation function:
```python
def validate_branch_has_read_flag(args: list[str]) -> None:
    """Raise ValueError if no read-only flag is present in branch args.

    Checks against BRANCH_ALLOWED_FLAGS — every allowed flag is a read-only
    flag, so any allowed flag proves read-only intent.
    Prevents bare `git branch <name>` from creating branches.
    """
```

## HOW
- Follow the exact same pattern as existing allowlists (frozenset of strings)
- `validate_branch_has_read_flag` is a separate function called by the future `git_branch()` — NOT inside `validate_args()`
- `_ALLOWLISTS` dict updated with all 7 new entries

## ALGORITHM (validate_branch_has_read_flag)
```
1. Extract all flags from args (items starting with "-")
2. Check if any flag (or its "=" prefix) is in BRANCH_ALLOWED_FLAGS
3. If none found → raise ValueError("git branch requires a read-only flag")
```

## DATA
- All allowlists: `frozenset[str]`
- `validate_branch_has_read_flag`: raises `ValueError` or returns `None`

## TESTS (write first)
In `test_arg_validation.py`, add test classes mirroring existing pattern:

- `TestValidateArgsFetchAllowed` — test `--prune`, `--tags`, `--verbose`, `--depth=1`
- `TestValidateArgsShowAllowed` — test `--format`, `--stat`, `--oneline`, `-p`
- `TestValidateArgsBranchAllowed` — test `--list`, `-a`, `-r`, `--contains`, `--show-current`
- `TestValidateArgsRevParseAllowed` — test `--abbrev-ref`, `--show-toplevel`, `--verify`
- `TestValidateArgsLsTreeAllowed` — test `-r`, `--name-only`, `--long`
- `TestValidateArgsLsFilesAllowed` — test `--cached`, `--others`, `--exclude-standard`
- `TestValidateArgsLsRemoteAllowed` — test `--heads`, `--tags`, `--get-url`
- `TestValidateArgsCrossCommandIsolation` — add cases for new commands (e.g. `--prune` rejected in `show`)
- `TestValidateBranchHasReadFlag` — test bare args rejected, `--list` passes, `-a` passes, `--show-current` passes
