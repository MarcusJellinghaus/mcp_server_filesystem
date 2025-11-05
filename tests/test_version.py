"""Test suite for version management utilities."""

import tempfile
from pathlib import Path

import pytest

from mcp_server_filesystem.version import (
    VersionError,
    VersionFormatError,
    VersionMismatchError,
    compare_versions,
    get_version_from_pyproject,
    is_prerelease,
    parse_version,
    validate_tag_matches_version,
    validate_version_format,
)


class TestGetVersionFromPyproject:
    """Tests for get_version_from_pyproject function."""

    def test_get_version_from_default_path(self):
        """Test reading version from default pyproject.toml."""
        version = get_version_from_pyproject()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_version_from_custom_path(self):
        """Test reading version from custom pyproject.toml path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pyproject_path = Path(tmpdir) / "pyproject.toml"
            pyproject_path.write_text(
                """
[project]
name = "test-package"
version = "1.2.3"
"""
            )

            version = get_version_from_pyproject(pyproject_path)
            assert version == "1.2.3"

    def test_get_version_with_prerelease(self):
        """Test reading pre-release version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pyproject_path = Path(tmpdir) / "pyproject.toml"
            pyproject_path.write_text(
                """
[project]
name = "test-package"
version = "1.2.3-rc1"
"""
            )

            version = get_version_from_pyproject(pyproject_path)
            assert version == "1.2.3-rc1"

    def test_get_version_file_not_found(self):
        """Test error when pyproject.toml doesn't exist."""
        with pytest.raises(FileNotFoundError):
            get_version_from_pyproject(Path("/nonexistent/pyproject.toml"))

    def test_get_version_missing_version_field(self):
        """Test error when version field is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pyproject_path = Path(tmpdir) / "pyproject.toml"
            pyproject_path.write_text(
                """
[project]
name = "test-package"
"""
            )

            with pytest.raises(VersionError):
                get_version_from_pyproject(pyproject_path)


class TestValidateVersionFormat:
    """Tests for validate_version_format function."""

    def test_valid_stable_version(self):
        """Test valid stable version formats."""
        assert validate_version_format("1.0.0")
        assert validate_version_format("0.1.0")
        assert validate_version_format("10.20.30")

    def test_valid_prerelease_versions(self):
        """Test valid pre-release version formats."""
        assert validate_version_format("1.0.0-alpha")
        assert validate_version_format("1.0.0-alpha1")
        assert validate_version_format("1.0.0-beta2")
        assert validate_version_format("1.0.0-rc")
        assert validate_version_format("1.0.0-rc1")

    def test_invalid_version_formats(self):
        """Test invalid version formats."""
        with pytest.raises(VersionFormatError):
            validate_version_format("invalid")  # Invalid string

        with pytest.raises(VersionFormatError):
            validate_version_format("")  # Empty string

        with pytest.raises(VersionFormatError):
            validate_version_format("1.0.0-gamma")  # Invalid pre-release identifier


class TestIsPrerelease:
    """Tests for is_prerelease function."""

    def test_stable_versions_not_prerelease(self):
        """Test that stable versions are not pre-releases."""
        assert not is_prerelease("1.0.0")
        assert not is_prerelease("0.1.0")
        assert not is_prerelease("10.20.30")

    def test_prerelease_versions(self):
        """Test pre-release version detection."""
        assert is_prerelease("1.0.0-alpha")
        assert is_prerelease("1.0.0-alpha1")
        assert is_prerelease("1.0.0-beta")
        assert is_prerelease("1.0.0-beta2")
        assert is_prerelease("1.0.0-rc")
        assert is_prerelease("1.0.0-rc1")


class TestParseVersion:
    """Tests for parse_version function."""

    def test_parse_stable_version(self):
        """Test parsing stable version."""
        major, minor, patch, prerelease = parse_version("1.2.3")
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert prerelease == ""

    def test_parse_prerelease_version(self):
        """Test parsing pre-release version."""
        major, minor, patch, prerelease = parse_version("1.2.3-rc1")
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert prerelease == "rc1"

    def test_parse_invalid_version(self):
        """Test parsing invalid version."""
        with pytest.raises(VersionFormatError):
            parse_version("invalid")


class TestCompareVersions:
    """Tests for compare_versions function."""

    def test_compare_equal_versions(self):
        """Test comparing equal versions."""
        assert compare_versions("1.0.0", "1.0.0") == 0
        assert compare_versions("1.2.3", "1.2.3") == 0

    def test_compare_different_major_versions(self):
        """Test comparing versions with different major numbers."""
        assert compare_versions("2.0.0", "1.0.0") == 1
        assert compare_versions("1.0.0", "2.0.0") == -1

    def test_compare_different_minor_versions(self):
        """Test comparing versions with different minor numbers."""
        assert compare_versions("1.2.0", "1.1.0") == 1
        assert compare_versions("1.1.0", "1.2.0") == -1

    def test_compare_different_patch_versions(self):
        """Test comparing versions with different patch numbers."""
        assert compare_versions("1.0.2", "1.0.1") == 1
        assert compare_versions("1.0.1", "1.0.2") == -1

    def test_compare_stable_vs_prerelease(self):
        """Test that stable versions are greater than pre-releases."""
        assert compare_versions("1.0.0", "1.0.0-rc1") == 1
        assert compare_versions("1.0.0-rc1", "1.0.0") == -1

    def test_compare_different_prereleases(self):
        """Test comparing different pre-release versions."""
        assert compare_versions("1.0.0-rc1", "1.0.0-alpha1") == 1
        assert compare_versions("1.0.0-alpha1", "1.0.0-rc1") == -1
        assert compare_versions("1.0.0-beta1", "1.0.0-alpha1") == 1


class TestValidateTagMatchesVersion:
    """Tests for validate_tag_matches_version function."""

    def test_matching_tag_and_version(self):
        """Test validation passes when tag matches version."""
        assert validate_tag_matches_version("v1.0.0", "1.0.0")
        assert validate_tag_matches_version("1.0.0", "1.0.0")

    def test_matching_prerelease_tag_and_version(self):
        """Test validation passes for pre-release versions."""
        assert validate_tag_matches_version("v1.0.0-rc1", "1.0.0-rc1")
        assert validate_tag_matches_version("1.0.0-alpha1", "1.0.0-alpha1")

    def test_mismatching_tag_and_version(self):
        """Test validation fails when tag doesn't match version."""
        with pytest.raises(VersionMismatchError):
            validate_tag_matches_version("v1.0.0", "1.0.1")

        with pytest.raises(VersionMismatchError):
            validate_tag_matches_version("v2.0.0", "1.0.0")

    def test_tag_without_v_prefix(self):
        """Test tag validation works without 'v' prefix."""
        assert validate_tag_matches_version("1.0.0", "1.0.0")

    def test_validate_tag_reads_pyproject_when_version_none(self):
        """Test that version is read from pyproject.toml when not provided."""
        # This will read the actual project version
        version = get_version_from_pyproject()
        assert validate_tag_matches_version(f"v{version}", None)


class TestPackageVersion:
    """Tests for package-level version export."""

    def test_version_is_accessible(self):
        """Test that __version__ is accessible from package."""
        from mcp_server_filesystem import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_matches_pyproject(self):
        """Test that package __version__ matches pyproject.toml."""
        from mcp_server_filesystem import __version__

        pyproject_version = get_version_from_pyproject()
        assert __version__ == pyproject_version
