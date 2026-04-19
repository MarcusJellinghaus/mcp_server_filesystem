# Step 1: Arg Validation Module

> **Context**: See `pr_info/steps/summary.md` for full architecture overview.

## LLM Prompt

```
Implement step 1 of issue #77 (read-only git operations).
Read pr_info/steps/summary.md for context, then read this step file.
Create the arg validation module with per-command allowlists and a validate function,
plus comprehensive unit tests. Follow TDD: write tests first, then implementation.
Run all code quality checks after implementation. Produce one commit.
```

## WHERE

- **New**: `src/mcp_workspace/git_operations/arg_validation.py`
- **New**: `tests/git_operations/test_arg_validation.py`

## WHAT

### `arg_validation.py`

```python
# Per-command allowlists (frozenset for immutability)
LOG_ALLOWED_FLAGS: frozenset[str]
DIFF_ALLOWED_FLAGS: frozenset[str]
STATUS_ALLOWED_FLAGS: frozenset[str]
MERGE_BASE_ALLOWED_FLAGS: frozenset[str]

# Map command name -> allowlist
_ALLOWLISTS: dict[str, frozenset[str]]

def validate_args(command: str, args: list[str]) -> None:
    """Validate args against per-command allowlist. Raises ValueError on rejection."""
```

## HOW

- No external imports needed — pure Python data + logic
- Exported via direct import: `from .arg_validation import validate_args`

## ALGORITHM — `validate_args`

```
1. Reject "--" in args (tool injects it internally for pathspec)
2. Look up allowlist for command (KeyError → ValueError if unknown command)
3. For each arg starting with "-":
     - Check if arg itself is in allowlist (e.g. "--staged")
     - If not, check if arg prefix before "=" is in allowlist (e.g. "--format=oneline")
     - If not, check if short flag prefix (first 2 chars) is in allowlist (e.g. "-n5" matches "-n")
     - If no match: raise ValueError with message:
       "Flag '{arg}' is not in the security allowlist for git_{command}. 
        If this flag should be supported, open an issue at 
        https://github.com/MarcusJellinghaus/mcp-workspace/issues"
4. Non-"-" args (refs, SHAs, ranges) pass through — git validates them
```

## DATA

### Allowlisted Flags

**`log`**: `--oneline`, `--format`, `--pretty`, `--abbrev-commit`, `--no-abbrev-commit`, `--date`, `--author`, `--committer`, `--grep`, `--invert-grep`, `--all-match`, `--since`, `--until`, `--after`, `--before`, `--all`, `--branches`, `--tags`, `--remotes`, `--merges`, `--no-merges`, `--first-parent`, `--max-count`, `-n`, `--skip`, `--reverse`, `--stat`, `--shortstat`, `--name-only`, `--name-status`, `--no-patch`, `--patch`, `-p`, `--graph`, `--decorate`, `--no-decorate`, `--follow`, `--diff-filter`, `--unified`, `-U`

**`diff`**: `--staged`, `--cached`, `--name-only`, `--name-status`, `--stat`, `--shortstat`, `--numstat`, `--no-patch`, `--patch`, `-p`, `--unified`, `-U`, `--diff-filter`, `--no-prefix`, `--word-diff`, `--word-diff-regex`, `--color-words`, `--ignore-space-change`, `-b`, `--ignore-all-space`, `-w`, `--ignore-blank-lines`, `--no-ext-diff`, `--no-textconv`, `--minimal`, `--patience`, `--histogram`, `--diff-algorithm`, `-M`, `-C`, `--find-renames`, `--find-copies`, `--relative`

**`status`**: `--short`, `-s`, `--long`, `--branch`, `-b`, `--porcelain`, `--verbose`, `-v`, `--untracked-files`, `-u`, `--ignored`, `--ignore-submodules`, `--show-stash`, `--ahead-behind`, `--no-ahead-behind`, `--renames`, `--no-renames`, `--find-renames`, `-z`, `--null`, `--column`, `--no-column`

**`merge_base`**: `--all`, `-a`, `--octopus`, `--independent`, `--is-ancestor`, `--fork-point`

### Return Value

- `validate_args` returns `None` on success (no return value)
- Raises `ValueError` with descriptive message on rejection

## TEST CASES (`test_arg_validation.py`)

```python
class TestValidateArgs:
    # Allowed flags pass through silently
    def test_log_allowed_flags(): ...         # --oneline, --format=short, -n5, --grep
    def test_diff_allowed_flags(): ...        # --staged, --cached, -M, --unified=3
    def test_status_allowed_flags(): ...      # --short, -s, -b, --porcelain
    def test_merge_base_allowed_flags(): ...  # --all, --is-ancestor, --fork-point

    # Non-flag args (refs, SHAs, ranges) pass through
    def test_refs_pass_through(): ...         # "main..HEAD", "abc1234", "origin/main"

    # Rejected flags raise ValueError
    def test_rejects_unknown_flag(): ...      # --output, --exec, --unknown
    def test_rejects_double_dash(): ...       # "--" in args
    def test_error_message_format(): ...      # contains flag name, command name, GitHub URL

    # Cross-command isolation
    def test_diff_flag_rejected_in_log(): ... # --staged not valid for log
    def test_log_flag_rejected_in_diff(): ... # --graph not valid for diff

    # Unknown command
    def test_unknown_command_raises(): ...    # "push" → ValueError

    # Flags with = values
    def test_flag_with_equals_value(): ...    # --format=oneline, --diff-algorithm=patience

    # Short flags with attached values
    def test_short_flag_with_value(): ...     # -n5, -U3
```
