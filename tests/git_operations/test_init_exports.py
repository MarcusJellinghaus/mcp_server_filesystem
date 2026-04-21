"""Tests for git_operations package __init__.py exports."""

from mcp_workspace import git_operations


def test_all_expected_symbols_exported() -> None:
    """Verify all symbols from __all__ are importable."""
    for name in git_operations.__all__:
        assert hasattr(git_operations, name), f"Missing export: {name}"


def test_expected_symbol_count() -> None:
    """Verify __all__ has the expected 33 symbols."""
    from mcp_workspace.git_operations import __all__

    assert len(__all__) == 33
