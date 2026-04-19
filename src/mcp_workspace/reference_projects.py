"""Reference project management — dataclass, URL normalization, and verification."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ReferenceProject:
    """A reference project with name, path, and optional URL."""

    name: str
    path: Path
    url: Optional[str] = None


def normalize_git_url(url: str) -> str:
    """Normalize a git URL for comparison.

    Converts SSH URLs to HTTPS, strips trailing .git and /,
    and lowercases the host portion.
    """
    url = url.strip()

    # Convert SSH format (git@host:org/repo.git) to HTTPS
    ssh_match = re.match(r"^git@([^:]+):(.+)$", url)
    if ssh_match:
        host = ssh_match.group(1)
        path = ssh_match.group(2)
        url = f"https://{host}/{path}"

    # Strip trailing .git
    if url.endswith(".git"):
        url = url[:-4]

    # Strip trailing /
    url = url.rstrip("/")

    # Lowercase the host portion
    if url.startswith("https://") or url.startswith("http://"):
        scheme_end = url.index("://") + 3
        rest = url[scheme_end:]
        if "/" in rest:
            host, path = rest.split("/", 1)
            url = f"{url[:scheme_end]}{host.lower()}/{path}"
        else:
            url = f"{url[:scheme_end]}{rest.lower()}"

    return url


def verify_url_match(explicit_url: str, detected_url: str, project_name: str) -> None:
    """Compare two URLs after normalization. Raises ValueError on mismatch."""
    if normalize_git_url(explicit_url) != normalize_git_url(detected_url):
        raise ValueError(
            f"URL mismatch for '{project_name}': "
            f"explicit '{explicit_url}' != detected '{detected_url}'"
        )


def detect_and_verify_url(
    path: Path, explicit_url: Optional[str], project_name: str
) -> Optional[str]:
    """Detect URL from git repo and/or verify against explicit URL.

    Returns the resolved URL (explicit or auto-detected), or None.
    Raises ValueError if explicit URL doesn't match detected URL.
    """
    from mcp_workspace.git_operations import is_git_repository
    from mcp_workspace.git_operations.remotes import get_remote_url

    if explicit_url and path.exists() and is_git_repository(path):
        detected = get_remote_url(path)
        if detected:
            verify_url_match(explicit_url, detected, project_name)
        return explicit_url

    if explicit_url and (not path.exists() or not is_git_repository(path)):
        return explicit_url  # will be used for lazy cloning

    if not explicit_url and path.exists() and is_git_repository(path):
        return get_remote_url(path)  # auto-detect, may be None

    return None  # no explicit URL, path doesn't exist or not a git repo
