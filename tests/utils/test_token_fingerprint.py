"""Tests for ``format_token_fingerprint``."""

from mcp_workspace.utils.token_fingerprint import format_token_fingerprint


def test_classic_pat() -> None:
    token = "ghp_" + "A" * 32 + "a3f9"
    assert len(token) == 40
    assert format_token_fingerprint(token) == "ghp_...a3f9"


def test_fine_grained_pat() -> None:
    token = "github_pat_" + "B" * 78 + "wxyz"
    assert len(token) == 93
    assert format_token_fingerprint(token) == "gith...wxyz"


def test_generic_long_token() -> None:
    token = "0123456789abcdef0123456789abcdef01234567"
    assert len(token) == 40
    assert format_token_fingerprint(token) == "0123...4567"


def test_length_9_just_over_threshold() -> None:
    token = "abcdEFGH9"
    assert format_token_fingerprint(token) == "abcd...FGH9"


def test_length_8_boundary() -> None:
    assert format_token_fingerprint("abcdefgh") == "****"


def test_length_1() -> None:
    assert format_token_fingerprint("x") == "****"


def test_empty_string() -> None:
    assert format_token_fingerprint("") == ""


def test_none() -> None:
    assert format_token_fingerprint(None) == ""


def test_raw_token_middle_not_leaked() -> None:
    token = "ghp_SECRET_MIDDLE_PART_ABC123xyz789a3f9"
    fp = format_token_fingerprint(token)
    assert "SECRET_MIDDLE_PART" not in fp


def test_short_token_not_leaked() -> None:
    token = "abcdefgh"
    fp = format_token_fingerprint(token)
    assert fp == "****"
    assert "abcdefgh" not in fp
    assert "a" not in fp
    assert "b" not in fp
    assert "c" not in fp
    assert "d" not in fp
    assert "e" not in fp
    assert "f" not in fp
    assert "g" not in fp
    assert "h" not in fp
