"""Version management utilities for mcp-server-filesystem."""

import re
from pathlib import Path
from typing import Tuple


class VersionError(Exception):
    """Exception raised for version-related errors."""

    pass


class VersionFormatError(VersionError):
    """Exception raised when version format is invalid."""

    pass


class VersionMismatchError(VersionError):
    """Exception raised when versions don't match."""

    pass


def get_version_from_pyproject(pyproject_path: Path | None = None) -> str:
    """
    Read version from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml. If None, uses package root.

    Returns:
        Version string from pyproject.toml

    Raises:
        VersionError: If pyproject.toml not found or version cannot be read
        FileNotFoundError: If pyproject.toml doesn't exist
    """
    if pyproject_path is None:
        # Default to package root
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    try:
        import tomli  # type: ignore
    except ImportError:
        # tomli is not available in runtime, only needed for version validation
        # Try reading manually as fallback
        content = pyproject_path.read_text()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return str(match.group(1))
        raise VersionError("Could not extract version from pyproject.toml")

    with open(pyproject_path, "rb") as f:
        try:
            import tomli

            data = tomli.load(f)
        except Exception as e:
            raise VersionError(f"Failed to parse pyproject.toml: {e}") from e

    try:
        version: str = data["project"]["version"]
    except KeyError as e:
        raise VersionError("Version not found in pyproject.toml") from e

    return version


def validate_version_format(version: str) -> bool:
    """
    Validate that version string follows semantic versioning.

    Args:
        version: Version string to validate

    Returns:
        True if version format is valid

    Raises:
        VersionFormatError: If version format is invalid
    """
    # Semantic versioning pattern: MAJOR.MINOR.PATCH with optional pre-release
    pattern = r"^\d+\.\d+\.\d+(?:-(alpha|beta|rc)\d*)?$"

    if not re.match(pattern, version):
        raise VersionFormatError(
            f"Invalid version format: {version}. "
            "Expected format: MAJOR.MINOR.PATCH[-prerelease]"
        )

    return True


def is_prerelease(version: str) -> bool:
    """
    Check if version is a pre-release.

    Args:
        version: Version string to check

    Returns:
        True if version contains pre-release identifier (alpha, beta, rc)
    """
    return bool(re.search(r"-(alpha|beta|rc)", version))


def parse_version(version: str) -> Tuple[int, int, int, str]:
    """
    Parse version string into components.

    Args:
        version: Version string to parse

    Returns:
        Tuple of (major, minor, patch, prerelease)
        prerelease is empty string for stable releases

    Raises:
        VersionFormatError: If version format is invalid
    """
    validate_version_format(version)

    # Split on hyphen to separate version from pre-release
    parts = version.split("-", 1)
    version_parts = parts[0].split(".")
    prerelease = parts[1] if len(parts) > 1 else ""

    major = int(version_parts[0])
    minor = int(version_parts[1])
    patch = int(version_parts[2])

    return major, minor, patch, prerelease


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2

    Raises:
        VersionFormatError: If either version format is invalid
    """
    v1_parts = parse_version(version1)
    v2_parts = parse_version(version2)

    # Compare major, minor, patch
    v1_major, v1_minor, v1_patch, v1_pre = v1_parts
    v2_major, v2_minor, v2_patch, v2_pre = v2_parts

    # Compare major version
    if v1_major < v2_major:
        return -1
    if v1_major > v2_major:
        return 1

    # Compare minor version
    if v1_minor < v2_minor:
        return -1
    if v1_minor > v2_minor:
        return 1

    # Compare patch version
    if v1_patch < v2_patch:
        return -1
    if v1_patch > v2_patch:
        return 1

    # If base versions are equal, compare pre-release
    # No pre-release (stable) is greater than any pre-release

    if not v1_pre and not v2_pre:
        return 0
    if not v1_pre:
        return 1
    if not v2_pre:
        return -1

    # Both have pre-release, compare them
    if v1_pre < v2_pre:
        return -1
    if v1_pre > v2_pre:
        return 1

    return 0


def validate_tag_matches_version(tag: str, version: str | None = None) -> bool:
    """
    Validate that a git tag matches the package version.

    Args:
        tag: Git tag (with or without 'v' prefix)
        version: Package version. If None, reads from pyproject.toml

    Returns:
        True if tag matches version

    Raises:
        VersionMismatchError: If tag doesn't match version
        VersionError: If version cannot be determined
    """
    if version is None:
        version = get_version_from_pyproject()

    # Remove 'v' prefix from tag if present
    tag_version = tag.lstrip("v")

    if tag_version != version:
        raise VersionMismatchError(
            f"Tag version ({tag_version}) does not match package version ({version})"
        )

    return True


# Package version - read from pyproject.toml
__version__ = get_version_from_pyproject()
