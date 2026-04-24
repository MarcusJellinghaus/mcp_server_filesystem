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


class TestSortOrder:
    """Tests for deterministic sort order: dirs first, alphabetical."""

    def test_dirs_before_files_alphabetical(self) -> None:
        """Dirs first at root, both groups alphabetical."""
        paths = ["z.py", "a.py", "tests/b.py", "src/x.py", "src/a.py"]
        result = list_directory_tree(paths)
        assert result == ["src/a.py", "src/x.py", "tests/b.py", "a.py", "z.py"]

    def test_sort_at_every_level(self) -> None:
        """Sort applies at every nesting level, not just root."""
        paths = [
            "src/z.py",
            "src/a.py",
            "src/utils/z.py",
            "src/utils/a.py",
            "src/core/x.py",
        ]
        result = list_directory_tree(paths)
        assert result == [
            "src/core/x.py",
            "src/utils/a.py",
            "src/utils/z.py",
            "src/a.py",
            "src/z.py",
        ]

    def test_dirs_only_false_no_dir_lines(self) -> None:
        """Default mode produces file paths only, no directory lines."""
        paths = ["src/a.py", "b.py"]
        result = list_directory_tree(paths, dirs_only=False)
        assert result == ["src/a.py", "b.py"]
        assert not any(entry.endswith("/") for entry in result)


class TestDirsOnlyMode:
    """Tests for dirs_only=True mode."""

    def test_dirs_only_basic(self) -> None:
        """Only directories shown, each with trailing /."""
        paths = ["z.py", "a.py", "tests/b.py", "src/x.py", "src/a.py"]
        result = list_directory_tree(paths, dirs_only=True)
        assert result == ["src/", "tests/"]

    def test_dirs_only_nested(self) -> None:
        """Nested dirs shown with full path and trailing /."""
        paths = ["src/utils/a.py", "src/core/b.py", "tests/test_a.py"]
        result = list_directory_tree(paths, dirs_only=True)
        assert result == ["src/", "src/core/", "src/utils/", "tests/"]

    def test_dirs_only_no_files(self) -> None:
        """Files completely excluded in dirs_only mode."""
        paths = ["a.py", "b.txt", "src/c.py"]
        result = list_directory_tree(paths, dirs_only=True)
        assert not any(not entry.endswith("/") for entry in result)
        assert "a.py" not in result
        assert "b.txt" not in result

    def test_dirs_only_with_base_path(self) -> None:
        """dirs_only works correctly with base_path."""
        paths = ["src/utils/a.py", "src/core/b.py"]
        result = list_directory_tree(paths, base_path="src", dirs_only=True)
        assert result == ["src/core/", "src/utils/"]
