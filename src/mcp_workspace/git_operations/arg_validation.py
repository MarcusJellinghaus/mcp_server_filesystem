"""Per-command argument validation for read-only git operations.

Validates CLI flags against allowlists to prevent injection of
dangerous flags (e.g. --exec, --output). Non-flag arguments (refs,
SHAs, ranges) pass through — git validates them.
"""

LOG_ALLOWED_FLAGS: frozenset[str] = frozenset(
    {
        "--oneline",
        "--format",
        "--pretty",
        "--abbrev-commit",
        "--no-abbrev-commit",
        "--date",
        "--author",
        "--committer",
        "--grep",
        "--invert-grep",
        "--all-match",
        "--since",
        "--until",
        "--after",
        "--before",
        "--all",
        "--branches",
        "--tags",
        "--remotes",
        "--merges",
        "--no-merges",
        "--first-parent",
        "--max-count",
        "-n",
        "--skip",
        "--reverse",
        "--stat",
        "--shortstat",
        "--name-only",
        "--name-status",
        "--no-patch",
        "--patch",
        "-p",
        "--graph",
        "--decorate",
        "--no-decorate",
        "--follow",
        "--diff-filter",
        "--unified",
        "-U",
        "--no-ext-diff",
        "--no-textconv",
    }
)

DIFF_ALLOWED_FLAGS: frozenset[str] = frozenset(
    {
        "--staged",
        "--cached",
        "--name-only",
        "--name-status",
        "--stat",
        "--shortstat",
        "--numstat",
        "--no-patch",
        "--patch",
        "-p",
        "--unified",
        "-U",
        "--diff-filter",
        "--no-prefix",
        "--word-diff",
        "--word-diff-regex",
        "--color-words",
        "--ignore-space-change",
        "-b",
        "--ignore-all-space",
        "-w",
        "--ignore-blank-lines",
        "--no-ext-diff",
        "--no-textconv",
        "--minimal",
        "--patience",
        "--histogram",
        "--diff-algorithm",
        "-M",
        "-C",
        "--find-renames",
        "--find-copies",
        "--relative",
    }
)

STATUS_ALLOWED_FLAGS: frozenset[str] = frozenset(
    {
        "--short",
        "-s",
        "--long",
        "--branch",
        "-b",
        "--porcelain",
        "--verbose",
        "-v",
        "--untracked-files",
        "-u",
        "--ignored",
        "--ignore-submodules",
        "--show-stash",
        "--ahead-behind",
        "--no-ahead-behind",
        "--renames",
        "--no-renames",
        "--find-renames",
        "-z",
        "--null",
        "--column",
        "--no-column",
    }
)

MERGE_BASE_ALLOWED_FLAGS: frozenset[str] = frozenset(
    {
        "--all",
        "-a",
        "--octopus",
        "--independent",
        "--is-ancestor",
        "--fork-point",
    }
)

_ALLOWLISTS: dict[str, frozenset[str]] = {
    "log": LOG_ALLOWED_FLAGS,
    "diff": DIFF_ALLOWED_FLAGS,
    "status": STATUS_ALLOWED_FLAGS,
    "merge_base": MERGE_BASE_ALLOWED_FLAGS,
}


def validate_args(command: str, args: list[str]) -> None:
    """Validate args against per-command allowlist.

    Non-flag arguments (refs, SHAs, ranges) pass through without
    validation — git validates them. Only flags (starting with ``-``)
    are checked.

    Args:
        command: Git sub-command name (e.g. "log", "diff").
        args: List of CLI arguments to validate.

    Raises:
        ValueError: If ``--`` is in args, command is unknown, or a
            flag is not in the allowlist.
    """
    if "--" in args:
        msg = (
            "Flag '--' is not allowed in args. " "Use the 'pathspec' parameter instead."
        )
        raise ValueError(msg)

    if command not in _ALLOWLISTS:
        msg = f"Unknown command: '{command}'"
        raise ValueError(msg)

    allowlist = _ALLOWLISTS[command]

    for arg in args:
        if not arg.startswith("-"):
            continue

        # Exact match
        if arg in allowlist:
            continue

        # --flag=value: check prefix before "="
        if "=" in arg:
            prefix = arg.split("=", 1)[0]
            if prefix in allowlist:
                continue

        # Short flag with attached value (e.g. -n5): check first 2 chars
        if len(arg) > 2 and not arg.startswith("--"):
            short_prefix = arg[:2]
            if short_prefix in allowlist:
                continue

        msg = (
            f"Flag '{arg}' is not in the security allowlist for git_{command}. "
            f"If this flag should be supported, open an issue at "
            f"https://github.com/MarcusJellinghaus/mcp-workspace/issues"
        )
        raise ValueError(msg)
