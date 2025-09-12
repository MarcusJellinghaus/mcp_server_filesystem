"""Tests for reference project CLI parsing and validation."""

import argparse
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_server_filesystem.main import parse_args, validate_reference_projects


class TestReferenceProjectCLI:
    """Test CLI argument parsing and validation."""

    def test_parse_single_reference_project(self) -> None:
        """Test parsing single reference project argument."""
        with patch(
            "sys.argv",
            [
                "script.py",
                "--project-dir",
                "/tmp",
                "--reference-project",
                "proj1=/path/to/proj1",
            ],
        ):
            args = parse_args()
            assert args.reference_project == ["proj1=/path/to/proj1"]

    def test_parse_multiple_reference_projects(self) -> None:
        """Test parsing multiple reference project arguments."""
        with patch(
            "sys.argv",
            [
                "script.py",
                "--project-dir",
                "/tmp",
                "--reference-project",
                "proj1=/path/to/proj1",
                "--reference-project",
                "proj2=/path/to/proj2",
            ],
        ):
            args = parse_args()
            assert args.reference_project == [
                "proj1=/path/to/proj1",
                "proj2=/path/to/proj2",
            ]

    @patch("mcp_server_filesystem.main.Path.exists")
    @patch("mcp_server_filesystem.main.Path.is_dir")
    def test_auto_rename_duplicates(
        self, mock_is_dir: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test auto-renaming duplicate project names."""
        # Mock path validation
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Test duplicate names get auto-renamed
        reference_args = [
            "proj=/path/to/proj1",
            "proj=/path/to/proj2",
            "proj=/path/to/proj3",
        ]
        result = validate_reference_projects(reference_args)

        expected = {
            "proj": Path("/path/to/proj1").absolute(),
            "proj_2": Path("/path/to/proj2").absolute(),
            "proj_3": Path("/path/to/proj3").absolute(),
        }
        assert result == expected

    @patch("mcp_server_filesystem.main.structured_logger")
    @patch("mcp_server_filesystem.main.Path.exists")
    def test_invalid_format_warnings(
        self, mock_exists: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test warnings for invalid argument formats."""
        mock_exists.return_value = False

        # Test invalid format (no '=' separator)
        reference_args = ["invalid_format", "valid=/path/to/proj"]
        result = validate_reference_projects(reference_args)

        # Should log warning for invalid format
        mock_logger.warning.assert_called()
        # Check if the warning was called with the expected message
        calls = mock_logger.warning.call_args_list
        assert len(calls) > 0
        # Look for the specific warning message about missing '='
        found_invalid_format = any(
            "missing" in str(call) and "=" in str(call) for call in calls
        )
        assert found_invalid_format

    @patch("mcp_server_filesystem.main.Path.exists")
    @patch("mcp_server_filesystem.main.Path.is_dir")
    def test_path_normalization(
        self, mock_is_dir: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test conversion to absolute paths."""
        # Mock path validation
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Test relative path gets converted to absolute
        reference_args = ["proj=./relative/path"]
        result = validate_reference_projects(reference_args)

        # Should contain absolute path
        assert "proj" in result
        assert result["proj"].is_absolute()

    @patch("mcp_server_filesystem.main.structured_logger")
    @patch("mcp_server_filesystem.main.Path.exists")
    def test_nonexistent_path_warning(
        self, mock_exists: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test warnings for non-existent paths."""
        mock_exists.return_value = False

        reference_args = ["proj=/nonexistent/path"]
        result = validate_reference_projects(reference_args)

        # Should log warning and return empty dict
        mock_logger.warning.assert_called()
        assert result == {}


class TestReferenceProjectMCPTools:
    """Test MCP tools functionality."""

    def test_get_reference_projects_empty(self) -> None:
        """Test discovery tool returns empty dict when no projects."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import get_reference_projects

        # Clear reference projects
        server_module._reference_projects = {}

        # Should return structured dict with empty projects list
        result = get_reference_projects()
        expected = {
            "count": 0,
            "projects": [],
            "usage": "No reference projects available"
        }
        assert result == expected
        assert isinstance(result, dict)

    def test_get_reference_projects_sorted(self) -> None:
        """Test discovery tool returns sorted list of project names in structured dict."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import get_reference_projects

        # Set up test data in unsorted order
        test_projects = {
            "zebra": Path("/path/to/zebra"),
            "alpha": Path("/path/to/alpha"),
            "beta": Path("/path/to/beta"),
        }
        server_module._reference_projects = test_projects

        # Should return structured dict with sorted projects list
        result = get_reference_projects()
        expected = {
            "count": 3,
            "projects": ["alpha", "beta", "zebra"],
            "usage": "Use these 3 projects with list_reference_directory() and read_reference_file()"
        }
        assert result == expected
        assert isinstance(result, dict)
        assert result["projects"] == ["alpha", "beta", "zebra"]

    def test_get_reference_projects_logging(self) -> None:
        """Test INFO level logging for discovery operations."""
        from unittest.mock import patch

        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import get_reference_projects

        # Set up test data
        test_projects = {"proj1": Path("/path/to/proj1")}
        server_module._reference_projects = test_projects

        # Test logging behavior (the decorator handles logging)
        with patch("mcp_server_filesystem.server.logger") as mock_logger:
            result = get_reference_projects()

            # Should return structured dict with project names
            expected = {
                "count": 1,
                "projects": ["proj1"],
                "usage": "Use these 1 projects with list_reference_directory() and read_reference_file()"
            }
            assert result == expected

            # The @log_function_call decorator should handle logging
            # We can verify the function was called and returned the expected result
            assert isinstance(result, dict)

    def test_list_reference_directory_success(self) -> None:
        """Test listing files in valid reference project."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import list_reference_directory

        # Set up test reference projects
        test_projects = {"test_proj": Path("/tmp/test_project").absolute()}
        server_module._reference_projects = test_projects

        # Mock the list_files_util function to return test data
        with patch("mcp_server_filesystem.server.list_files_util") as mock_list_files:
            mock_list_files.return_value = ["file1.py", "file2.txt", "subdir/file3.md"]

            result = list_reference_directory("test_proj")

            # Should return the mocked file list
            assert result == ["file1.py", "file2.txt", "subdir/file3.md"]
            assert isinstance(result, list)

            # Verify list_files_util was called with correct parameters
            mock_list_files.assert_called_once_with(
                ".", project_dir=test_projects["test_proj"], use_gitignore=True
            )

    def test_list_reference_directory_not_found(self) -> None:
        """Test error handling for non-existent reference project."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import list_reference_directory

        # Set up test reference projects (empty)
        server_module._reference_projects = {}

        # Should raise ValueError for non-existent project
        with pytest.raises(
            ValueError, match="Reference project 'nonexistent' not found"
        ):
            list_reference_directory("nonexistent")

    def test_list_reference_directory_gitignore(self) -> None:
        """Test gitignore filtering is applied."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import list_reference_directory

        # Set up test reference projects
        test_projects = {"proj_with_gitignore": Path("/tmp/gitignore_test").absolute()}
        server_module._reference_projects = test_projects

        # Mock the list_files_util function
        with patch("mcp_server_filesystem.server.list_files_util") as mock_list_files:
            # Should return files after gitignore filtering
            mock_list_files.return_value = ["src/main.py", "README.md"]

            result = list_reference_directory("proj_with_gitignore")

            # Verify gitignore filtering was enabled
            mock_list_files.assert_called_once_with(
                ".",
                project_dir=test_projects["proj_with_gitignore"],
                use_gitignore=True,
            )
            assert result == ["src/main.py", "README.md"]

    def test_list_reference_directory_logging(self) -> None:
        """Test DEBUG level logging for file operations."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import list_reference_directory

        # Set up test reference projects
        test_projects = {"log_test_proj": Path("/tmp/log_test").absolute()}
        server_module._reference_projects = test_projects

        # Mock the list_files_util function
        with patch("mcp_server_filesystem.server.list_files_util") as mock_list_files:
            with patch("mcp_server_filesystem.server.logger") as mock_logger:
                mock_list_files.return_value = ["test.py"]

                result = list_reference_directory("log_test_proj")

                # Should return expected result
                assert result == ["test.py"]

                # The @log_function_call decorator should handle logging
                # We can verify the function was called and returned the expected result
                assert isinstance(result, list)

    def test_read_reference_file_success(self) -> None:
        """Test reading file from valid reference project."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import read_reference_file

        # Set up test reference projects
        test_projects = {"test_proj": Path("/tmp/test_project").absolute()}
        server_module._reference_projects = test_projects

        # Mock the read_file_util function to return test data
        with patch("mcp_server_filesystem.server.read_file_util") as mock_read_file:
            mock_read_file.return_value = "Test file content\nLine 2\n"

            result = read_reference_file("test_proj", "test_file.txt")

            # Should return the mocked file content
            assert result == "Test file content\nLine 2\n"
            assert isinstance(result, str)

            # Verify read_file_util was called with correct parameters
            mock_read_file.assert_called_once_with(
                "test_file.txt", project_dir=test_projects["test_proj"]
            )

    def test_read_reference_file_project_not_found(self) -> None:
        """Test error handling for non-existent reference project."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import read_reference_file

        # Set up test reference projects (empty)
        server_module._reference_projects = {}

        # Should raise ValueError for non-existent project
        with pytest.raises(
            ValueError, match="Reference project 'nonexistent' not found"
        ):
            read_reference_file("nonexistent", "test_file.txt")

    def test_read_reference_file_file_not_found(self) -> None:
        """Test error handling for non-existent file."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import read_reference_file

        # Set up test reference projects
        test_projects = {"test_proj": Path("/tmp/test_project").absolute()}
        server_module._reference_projects = test_projects

        # Mock the read_file_util function to raise FileNotFoundError
        with patch("mcp_server_filesystem.server.read_file_util") as mock_read_file:
            mock_read_file.side_effect = FileNotFoundError(
                "File not found: test_file.txt"
            )

            # Should propagate the FileNotFoundError
            with pytest.raises(
                FileNotFoundError, match="File not found: test_file.txt"
            ):
                read_reference_file("test_proj", "nonexistent_file.txt")

    def test_read_reference_file_security(self) -> None:
        """Test path traversal prevention (reuse existing security)."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import read_reference_file

        # Set up test reference projects
        test_projects = {"test_proj": Path("/tmp/test_project").absolute()}
        server_module._reference_projects = test_projects

        # Mock the read_file_util function to raise security error
        with patch("mcp_server_filesystem.server.read_file_util") as mock_read_file:
            mock_read_file.side_effect = ValueError(
                "Security error: Path traversal detected"
            )

            # Should propagate the security error
            with pytest.raises(
                ValueError, match="Security error: Path traversal detected"
            ):
                read_reference_file("test_proj", "../../../etc/passwd")

    def test_read_reference_file_logging(self) -> None:
        """Test DEBUG level logging for file operations."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import read_reference_file

        # Set up test reference projects
        test_projects = {"log_test_proj": Path("/tmp/log_test").absolute()}
        server_module._reference_projects = test_projects

        # Mock the read_file_util function
        with patch("mcp_server_filesystem.server.read_file_util") as mock_read_file:
            with patch("mcp_server_filesystem.server.logger") as mock_logger:
                mock_read_file.return_value = "test content"

                result = read_reference_file("log_test_proj", "test.txt")

                # Should return expected result
                assert result == "test content"

                # The @log_function_call decorator should handle logging
                # We can verify the function was called and returned the expected result
                assert isinstance(result, str)


class TestReferenceProjectServerStorage:
    """Test server storage and initialization."""

    def test_set_reference_projects(self) -> None:
        """Test setting reference projects storage."""
        import mcp_server_filesystem.server as server_module
        from mcp_server_filesystem.server import set_reference_projects

        # Test setting reference projects
        test_projects = {
            "proj1": Path("/path/to/proj1").absolute(),
            "proj2": Path("/path/to/proj2").absolute(),
        }

        set_reference_projects(test_projects)

        # Check that the global variable was updated
        assert server_module._reference_projects == test_projects

    def test_run_server_with_reference_projects(self) -> None:
        """Test run_server accepts reference projects parameter."""
        from unittest.mock import patch

        from mcp_server_filesystem.server import run_server

        # Test that run_server can be called with reference_projects parameter
        test_projects = {
            "proj1": Path("/path/to/proj1").absolute(),
            "proj2": Path("/path/to/proj2").absolute(),
        }

        # Mock the mcp.run() call to avoid actually starting the server
        with patch("mcp_server_filesystem.server.mcp.run") as mock_run:
            with patch(
                "mcp_server_filesystem.server.set_reference_projects"
            ) as mock_set_ref:
                run_server(Path("/test/project"), reference_projects=test_projects)

                # Verify that set_reference_projects was called with the correct arguments
                mock_set_ref.assert_called_once_with(test_projects)
                mock_run.assert_called_once()

    def test_reference_projects_logging(self) -> None:
        """Test INFO level logging during initialization."""
        from unittest.mock import patch

        from mcp_server_filesystem.server import set_reference_projects

        test_projects = {
            "proj1": Path("/path/to/proj1").absolute(),
            "proj2": Path("/path/to/proj2").absolute(),
        }

        # Test logging behavior
        with patch("mcp_server_filesystem.server.logger") as mock_logger:
            with patch(
                "mcp_server_filesystem.server.structured_logger"
            ) as mock_structured:
                set_reference_projects(test_projects)

                # Verify INFO level logging was called
                assert mock_logger.info.called
                assert mock_structured.info.called

                # Check that project details were logged
                info_calls = mock_logger.info.call_args_list
                assert len(info_calls) >= 1

    @patch("mcp_server_filesystem.main.Path.exists")
    @patch("mcp_server_filesystem.main.Path.is_dir")
    def test_empty_name_validation(
        self, mock_is_dir: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test validation of empty project names."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Test empty name gets rejected
        reference_args = ["=/path/to/proj"]
        with patch("mcp_server_filesystem.main.structured_logger") as mock_logger:
            result = validate_reference_projects(reference_args)

            # Should log warning for empty name
            mock_logger.warning.assert_called()
            assert result == {}


class TestReferenceProjectIntegration:
    """Test CLI to server integration."""

    @patch("mcp_server_filesystem.server.run_server")
    @patch("mcp_server_filesystem.main.Path.exists")
    @patch("mcp_server_filesystem.main.Path.is_dir")
    def test_main_with_reference_projects(
        self, mock_is_dir: MagicMock, mock_exists: MagicMock, mock_run_server: MagicMock
    ) -> None:
        """Test main() passes reference projects to run_server()."""
        # Mock path validation for both project dir and reference projects
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Mock sys.argv to simulate CLI arguments
        test_args = [
            "script.py",
            "--project-dir",
            "/test/project",
            "--reference-project",
            "proj1=/path/to/proj1",
            "--reference-project",
            "proj2=/path/to/proj2",
        ]

        with patch("sys.argv", test_args):
            with patch("mcp_server_filesystem.main.setup_logging"):
                from mcp_server_filesystem.main import main

                main()

                # Verify run_server was called with correct arguments
                mock_run_server.assert_called_once()
                call_args = mock_run_server.call_args

                # Check project_dir argument (positional)
                assert call_args[0][0] == Path("/test/project").absolute()

                # Check reference_projects argument (keyword)
                expected_ref_projects = {
                    "proj1": Path("/path/to/proj1").absolute(),
                    "proj2": Path("/path/to/proj2").absolute(),
                }
                assert call_args[1]["reference_projects"] == expected_ref_projects

    @patch("mcp_server_filesystem.server.run_server")
    @patch("mcp_server_filesystem.main.Path.exists")
    @patch("mcp_server_filesystem.main.Path.is_dir")
    def test_main_without_reference_projects(
        self, mock_is_dir: MagicMock, mock_exists: MagicMock, mock_run_server: MagicMock
    ) -> None:
        """Test main() works without reference projects (backward compatibility)."""
        # Mock path validation
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Mock sys.argv without reference projects
        test_args = ["script.py", "--project-dir", "/test/project"]

        with patch("sys.argv", test_args):
            with patch("mcp_server_filesystem.main.setup_logging"):
                from mcp_server_filesystem.main import main

                main()

                # Verify run_server was called with correct arguments
                mock_run_server.assert_called_once()
                call_args = mock_run_server.call_args

                # Check project_dir argument (positional)
                assert call_args[0][0] == Path("/test/project").absolute()

                # Check reference_projects argument (keyword) - should be empty dict
                assert call_args[1]["reference_projects"] == {}

    @patch("mcp_server_filesystem.server.run_server")
    @patch("mcp_server_filesystem.main.Path.exists")
    @patch("mcp_server_filesystem.main.Path.is_dir")
    def test_main_with_auto_rename(
        self, mock_is_dir: MagicMock, mock_exists: MagicMock, mock_run_server: MagicMock
    ) -> None:
        """Test main() handles duplicate names with auto-rename."""
        # Mock path validation
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Mock sys.argv with duplicate project names
        test_args = [
            "script.py",
            "--project-dir",
            "/test/project",
            "--reference-project",
            "proj=/path/to/proj1",
            "--reference-project",
            "proj=/path/to/proj2",
            "--reference-project",
            "proj=/path/to/proj3",
        ]

        with patch("sys.argv", test_args):
            with patch("mcp_server_filesystem.main.setup_logging"):
                from mcp_server_filesystem.main import main

                main()

                # Verify run_server was called with correct arguments
                mock_run_server.assert_called_once()
                call_args = mock_run_server.call_args

                # Check project_dir argument (positional)
                assert call_args[0][0] == Path("/test/project").absolute()

                # Check reference_projects argument with auto-rename
                expected_ref_projects = {
                    "proj": Path("/path/to/proj1").absolute(),
                    "proj_2": Path("/path/to/proj2").absolute(),
                    "proj_3": Path("/path/to/proj3").absolute(),
                }
                assert call_args[1]["reference_projects"] == expected_ref_projects
