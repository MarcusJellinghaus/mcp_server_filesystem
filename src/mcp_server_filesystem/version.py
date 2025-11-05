"""Version management utilities for mcp-server-filesystem."""

import re
from pathlib import Path

from packaging.version import InvalidVersion, Version  # type: ignore[import-not-found]


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
        import tomli  # type: ignore[import-not-found]
    except ImportError:
        # tomli is not available, try reading manually as fallback
        content = pyproject_path.read_text()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return str(match.group(1))
        raise VersionError("Could not extract version from pyproject.toml")

    with open(pyproject_path, "rb") as f:
        try:
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
    Validate that version string is valid.

    Args:
        version: Version string to validate

    Returns:
        True if version format is valid

    Raises:
        VersionFormatError: If version format is invalid
    """
    try:
        Version(version)
        return True
    except InvalidVersion as e:
        raise VersionFormatError(
            f"Invalid version format: {version}. Error: {e}"
        ) from e


def is_prerelease(version: str) -> bool:
    """
    Check if version is a pre-release.

    Args:
        version: Version string to check

    Returns:
        True if version is a pre-release
    """
    try:
        return bool(Version(version).is_prerelease)
    except InvalidVersion:
        return False


def parse_version(version: str) -> tuple[int, int, int, str]:
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
    v = Version(version)

    major = v.release[0] if len(v.release) > 0 else 0
    minor = v.release[1] if len(v.release) > 1 else 0
    patch = v.release[2] if len(v.release) > 2 else 0

    prerelease = ""
    if v.is_prerelease and v.pre:
        prerelease_type, prerelease_num = v.pre
        prerelease = f"{prerelease_type}{prerelease_num}"

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
    try:
        v1 = Version(version1)
        v2 = Version(version2)
    except InvalidVersion as e:
        raise VersionFormatError(f"Invalid version format: {e}") from e

    if v1 < v2:
        return -1
    if v1 > v2:
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
