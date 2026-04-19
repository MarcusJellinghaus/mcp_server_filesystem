"""Tests for git argument validation against per-command allowlists."""

import pytest

from mcp_workspace.git_operations.arg_validation import validate_args


class TestValidateArgsLogAllowed:
    """Allowed log flags pass through silently."""

    def test_oneline(self) -> None:
        validate_args("log", ["--oneline"])

    def test_format_with_value(self) -> None:
        validate_args("log", ["--format=short"])

    def test_short_n_with_value(self) -> None:
        validate_args("log", ["-n5"])

    def test_grep(self) -> None:
        validate_args("log", ["--grep", "fix"])

    def test_multiple_flags(self) -> None:
        validate_args("log", ["--oneline", "--graph", "--all", "-n10"])


class TestValidateArgsDiffAllowed:
    """Allowed diff flags pass through silently."""

    def test_staged(self) -> None:
        validate_args("diff", ["--staged"])

    def test_cached(self) -> None:
        validate_args("diff", ["--cached"])

    def test_rename_detection(self) -> None:
        validate_args("diff", ["-M"])

    def test_unified_with_value(self) -> None:
        validate_args("diff", ["--unified=3"])

    def test_diff_algorithm_equals(self) -> None:
        validate_args("diff", ["--diff-algorithm=patience"])


class TestValidateArgsStatusAllowed:
    """Allowed status flags pass through silently."""

    def test_short(self) -> None:
        validate_args("status", ["--short"])

    def test_short_alias(self) -> None:
        validate_args("status", ["-s"])

    def test_branch_short(self) -> None:
        validate_args("status", ["-b"])

    def test_porcelain(self) -> None:
        validate_args("status", ["--porcelain"])


class TestValidateArgsMergeBaseAllowed:
    """Allowed merge-base flags pass through silently."""

    def test_all(self) -> None:
        validate_args("merge_base", ["--all"])

    def test_is_ancestor(self) -> None:
        validate_args("merge_base", ["--is-ancestor"])

    def test_fork_point(self) -> None:
        validate_args("merge_base", ["--fork-point"])


class TestValidateArgsRefsPassThrough:
    """Non-flag args (refs, SHAs, ranges) pass through without validation."""

    def test_branch_name(self) -> None:
        validate_args("log", ["main"])

    def test_sha(self) -> None:
        validate_args("log", ["abc1234"])

    def test_range(self) -> None:
        validate_args("log", ["main..HEAD"])

    def test_remote_ref(self) -> None:
        validate_args("diff", ["origin/main"])

    def test_empty_args(self) -> None:
        validate_args("log", [])


class TestValidateArgsRejected:
    """Unknown or dangerous flags raise ValueError."""

    def test_rejects_unknown_flag(self) -> None:
        with pytest.raises(ValueError, match="--output"):
            validate_args("log", ["--output"])

    def test_rejects_exec_flag(self) -> None:
        with pytest.raises(ValueError, match="--exec"):
            validate_args("diff", ["--exec"])

    def test_rejects_double_dash(self) -> None:
        with pytest.raises(ValueError, match="--"):
            validate_args("log", ["--"])

    def test_error_message_contains_command(self) -> None:
        with pytest.raises(ValueError, match="git_log"):
            validate_args("log", ["--unknown"])

    def test_error_message_contains_github_url(self) -> None:
        with pytest.raises(ValueError, match="github.com"):
            validate_args("log", ["--unknown"])


class TestValidateArgsCrossCommandIsolation:
    """Flags valid for one command must not work in another."""

    def test_staged_rejected_in_log(self) -> None:
        with pytest.raises(ValueError, match="--staged"):
            validate_args("log", ["--staged"])

    def test_graph_rejected_in_diff(self) -> None:
        with pytest.raises(ValueError, match="--graph"):
            validate_args("diff", ["--graph"])

    def test_porcelain_rejected_in_merge_base(self) -> None:
        with pytest.raises(ValueError, match="--porcelain"):
            validate_args("merge_base", ["--porcelain"])


class TestValidateArgsUnknownCommand:
    """Unknown commands raise ValueError."""

    def test_push_rejected(self) -> None:
        with pytest.raises(ValueError, match="push"):
            validate_args("push", [])

    def test_reset_rejected(self) -> None:
        with pytest.raises(ValueError, match="reset"):
            validate_args("reset", ["--hard"])


class TestValidateArgsFlagEqualsValue:
    """Flags with = values are matched by prefix."""

    def test_format_equals_oneline(self) -> None:
        validate_args("log", ["--format=oneline"])

    def test_diff_algorithm_equals_patience(self) -> None:
        validate_args("diff", ["--diff-algorithm=patience"])

    def test_date_equals_relative(self) -> None:
        validate_args("log", ["--date=relative"])


class TestValidateArgsShortFlagWithValue:
    """Short flags with attached values matched by 2-char prefix."""

    def test_n5(self) -> None:
        validate_args("log", ["-n5"])

    def test_u3(self) -> None:
        validate_args("diff", ["-U3"])

    def test_short_untracked(self) -> None:
        validate_args("status", ["-u"])
