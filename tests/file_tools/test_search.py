"""Tests for search_files glob-only, content search, and combined modes."""

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


class TestSearchFilesContentSearch:
    """Tests for content search (regex) and combined modes."""

    def test_search_files_pattern_finds_content(self, project_dir: Path) -> None:
        """Regex pattern matches correct lines in files."""
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("def hello():\n    return 42\n")
        (src_dir / "util.py").write_text("x = 1\ndef world():\n    pass\n")

        result = search_files(project_dir, glob="src/*.py", pattern=r"def \w+")

        assert result["mode"] == "content_search"
        assert result["truncated"] is False
        assert result["total_matches"] == 2
        texts = [m["text"] for m in result["details"]]
        assert any("def hello" in t for t in texts)
        assert any("def world" in t for t in texts)

    def test_search_files_pattern_no_matches(self, project_dir: Path) -> None:
        """Regex that matches nothing returns empty matches list."""
        (project_dir / "empty.py").write_text("x = 1\n")

        result = search_files(project_dir, pattern=r"zzz_no_match_zzz")

        assert result["mode"] == "content_search"
        assert result["details"] == []
        assert result["total_matches"] == 0
        assert result["truncated"] is False

    def test_search_files_invalid_regex_raises(self, project_dir: Path) -> None:
        """Bad regex pattern raises ValueError."""
        with pytest.raises(ValueError, match="Invalid regex"):
            search_files(project_dir, pattern=r"[invalid")

    def test_search_files_combined_mode(self, project_dir: Path) -> None:
        """Glob + pattern filters both file paths and content."""
        d = project_dir / "combo"
        d.mkdir()
        (d / "app.py").write_text("def run():\n    pass\n")
        (d / "app.txt").write_text("def run():\n    pass\n")
        (d / "lib.py").write_text("x = 1\n")

        result = search_files(project_dir, glob="**/*.py", pattern=r"def run")

        assert result["mode"] == "content_search"
        files = [m["file"] for m in result["details"]]
        assert any("app.py" in f for f in files)
        # app.txt should NOT match (glob filters it out)
        assert not any("app.txt" in f for f in files)
        # lib.py should NOT match (pattern filters it out)
        assert not any("lib.py" in f for f in files)

    def test_search_files_context_lines(self, project_dir: Path) -> None:
        """Surrounding lines included in text field with context_lines."""
        (project_dir / "ctx.py").write_text("line1\nline2\nMATCH_HERE\nline4\nline5\n")

        result = search_files(project_dir, pattern=r"MATCH_HERE", context_lines=1)

        assert len(result["details"]) == 1
        match = result["details"][0]
        assert match["line"] == 3
        assert "line2" in match["text"]
        assert "MATCH_HERE" in match["text"]
        assert "line4" in match["text"]

    def test_search_files_max_result_lines_truncation(self, project_dir: Path) -> None:
        """Verify max_result_lines cap triggers truncated: True."""
        # Create file with many matchable lines
        lines = [f"match_line_{i}" for i in range(20)]
        (project_dir / "many.txt").write_text("\n".join(lines) + "\n")

        result = search_files(
            project_dir,
            pattern=r"match_line_",
            max_results=100,
            max_result_lines=5,
        )

        assert result["truncated"] is True
        # Should have stopped at or before 5 lines
        total_lines = sum(m["text"].count("\n") + 1 for m in result["details"])
        assert total_lines <= 5
        assert result["total_matches"] == 20

    def test_search_files_skips_binary_files(self, project_dir: Path) -> None:
        """Binary file with non-UTF-8 bytes is skipped without error."""
        (project_dir / "text.py").write_text("def hello():\n    pass\n")
        (project_dir / "binary.bin").write_bytes(b"\x80\x81\x82\xff\xfe")

        result = search_files(project_dir, pattern=r"def hello")

        assert result["mode"] == "content_search"
        assert len(result["details"]) == 1
        assert "text.py" in result["details"][0]["file"]


class TestSearchFilesLineTruncation:
    """Tests for per-line truncation of long lines."""

    def test_long_line_truncated_at_500_chars(self, project_dir: Path) -> None:
        """A line exceeding 500 chars is truncated with marker."""
        long_line = "x" * 1000
        (project_dir / "long.txt").write_text(long_line + "\n")

        result = search_files(project_dir, pattern=r"x+")

        detail = result["details"][0]
        assert len(detail["text"]) < 1000
        assert "... [truncated, line has 1000 chars]" in detail["text"]
        assert detail["text"].startswith("x" * 500)

    def test_short_line_not_truncated(self, project_dir: Path) -> None:
        """A line under 500 chars is returned as-is."""
        line = "y" * 499
        (project_dir / "short.txt").write_text(line + "\n")

        result = search_files(project_dir, pattern=r"y+")

        assert result["details"][0]["text"] == line
        assert "truncated" not in result["details"][0]["text"]

    def test_context_lines_also_truncated(self, project_dir: Path) -> None:
        """Context lines (not just match line) are truncated too."""
        long_ctx = "a" * 800
        (project_dir / "ctx.txt").write_text(f"{long_ctx}\nMATCH\nshort\n")

        result = search_files(project_dir, pattern=r"MATCH", context_lines=1)

        text = result["details"][0]["text"]
        lines = text.split("\n")
        # First line (context) should be truncated
        assert "... [truncated, line has 800 chars]" in lines[0]
        # Match line should be intact
        assert lines[1] == "MATCH"
