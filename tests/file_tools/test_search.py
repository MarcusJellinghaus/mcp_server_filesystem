"""Tests for search_files glob-only file search mode."""

from pathlib import Path

import pytest

from mcp_workspace.file_tools.search import search_files


class TestSearchFilesGlobOnly:
    """Tests for file search (glob-only) mode."""

    def test_search_files_no_args_raises(self, project_dir: Path) -> None:
        """Neither glob nor pattern provided raises ValueError."""
        with pytest.raises(ValueError, match="At least one of 'glob' or 'pattern'"):
            search_files(project_dir)

    def test_search_files_glob_finds_files(self, project_dir: Path) -> None:
        """Glob pattern matches only the expected file types."""
        search_dir = project_dir / "search_test"
        search_dir.mkdir()
        (search_dir / "app.py").write_text("print('hello')")
        (search_dir / "utils.py").write_text("x = 1")
        (search_dir / "readme.txt").write_text("docs")

        result = search_files(project_dir, glob="**/*.py")

        assert result["mode"] == "file_search"
        assert result["truncated"] is False
        matched = result["files"]
        # Our created .py files should be in the results
        matched_basenames = {Path(f).name for f in matched}
        assert "app.py" in matched_basenames
        assert "utils.py" in matched_basenames
        assert "readme.txt" not in matched_basenames

    def test_search_files_glob_no_matches(self, project_dir: Path) -> None:
        """Glob that matches nothing returns empty files list."""
        result = search_files(project_dir, glob="**/*.nonexistent_extension_xyz")

        assert result["mode"] == "file_search"
        assert result["files"] == []
        assert result["total_files"] == 0
        assert result["truncated"] is False

    def test_search_files_glob_max_results(self, project_dir: Path) -> None:
        """Verify max_results truncation and truncated flag."""
        bulk_dir = project_dir / "bulk"
        bulk_dir.mkdir()
        for i in range(10):
            (bulk_dir / f"file_{i}.dat").write_text(f"data {i}")

        result = search_files(project_dir, glob="**/*.dat", max_results=3)

        assert result["mode"] == "file_search"
        assert len(result["files"]) == 3
        assert result["total_files"] == 10
        assert result["truncated"] is True

    def test_search_files_glob_respects_gitignore(self, project_dir: Path) -> None:
        """Files matching .gitignore patterns are excluded."""
        (project_dir / ".gitignore").write_text("*.log\n")
        log_dir = project_dir / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text("log entry")
        (log_dir / "debug.log").write_text("debug entry")
        (log_dir / "keep.txt").write_text("keep me")

        result = search_files(project_dir, glob="logs/*")

        matched_names = {Path(f).name for f in result["files"]}
        assert "keep.txt" in matched_names
        assert "app.log" not in matched_names
        assert "debug.log" not in matched_names
