"""Tests for tree_listing module."""

from mcp_workspace.file_tools.tree_listing import list_directory_tree


class TestListDirectoryTree:
    """Tests for list_directory_tree public API."""

    def test_empty_input(self) -> None:
        """Empty input returns empty list."""
        assert list_directory_tree([]) == []

    def test_flat_files_only(self) -> None:
        """Flat files with no subdirs are returned as-is."""
        paths = ["a.py", "b.py", "c.txt"]
        result = list_directory_tree(paths)
        assert sorted(result) == sorted(paths)

    def test_nested_structure(self) -> None:
        """All paths preserved through tree round-trip."""
        paths = ["src/a.py", "src/b.py", "tests/test_a.py"]
        result = list_directory_tree(paths)
        assert sorted(result) == sorted(paths)

    def test_base_path_stripping(self) -> None:
        """base_path is stripped internally but preserved in output."""
        paths = ["src/utils/a.py", "src/utils/b.py"]
        result = list_directory_tree(paths, base_path="src")
        assert sorted(result) == sorted(paths)

    def test_deeply_nested(self) -> None:
        """Deeply nested path round-trips correctly."""
        paths = ["a/b/c/d/file.txt"]
        result = list_directory_tree(paths)
        assert result == paths

    def test_base_path_dot_is_noop(self) -> None:
        """base_path='.' works as a no-op."""
        paths = ["src/a.py", "tests/test_a.py"]
        result = list_directory_tree(paths, base_path=".")
        assert sorted(result) == sorted(paths)

    def test_base_path_empty_is_noop(self) -> None:
        """base_path='' works as a no-op."""
        paths = ["src/a.py", "tests/test_a.py"]
        result = list_directory_tree(paths, base_path="")
        assert sorted(result) == sorted(paths)

    def test_base_path_with_trailing_slash(self) -> None:
        """base_path with trailing slash works correctly."""
        paths = ["src/utils/a.py"]
        result = list_directory_tree(paths, base_path="src/")
        assert result == paths

    def test_multiple_files_in_nested_dirs(self) -> None:
        """Multiple files across multiple nested directories."""
        paths = [
            "src/a.py",
            "src/utils/b.py",
            "src/utils/helpers/c.py",
            "tests/test_a.py",
            "README.md",
        ]
        result = list_directory_tree(paths)
        assert sorted(result) == sorted(paths)
