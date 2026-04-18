"""Tests for mcp_workspace.constants module."""

from mcp_workspace.constants import DUPLICATE_PROTECTION_SECONDS


def test_duplicate_protection_seconds_is_positive_int() -> None:
    assert isinstance(DUPLICATE_PROTECTION_SECONDS, int)
    assert DUPLICATE_PROTECTION_SECONDS > 0


def test_duplicate_protection_seconds_value() -> None:
    assert DUPLICATE_PROTECTION_SECONDS == 60
