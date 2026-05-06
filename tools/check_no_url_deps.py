"""Fail if pyproject.toml [project] dependencies contain direct URL specs.

Direct URL dependencies (e.g. ``pkg @ git+https://...``) are not allowed in
``[project].dependencies`` or ``[project.optional-dependencies]``. PyPI and
``twine check`` reject sdists/wheels that include them, and they make the
project install non-portable.

Use ``[tool.mcp-coder.install-from-github]`` for pre-installing GitHub
sources via ``tools/reinstall_local.bat`` and the CI install step instead.
"""

import sys
import tomllib
from pathlib import Path


def main() -> int:
    """Return 1 if any direct URL dependency is found, else 0."""
    project_dir = Path(__file__).resolve().parent.parent
    path = project_dir / "pyproject.toml"

    with open(path, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    sources: list[tuple[str, str]] = []
    for dep in project.get("dependencies", []):
        sources.append(("dependencies", dep))
    for group, items in project.get("optional-dependencies", {}).items():
        for dep in items:
            sources.append((f"optional-dependencies.{group}", dep))

    bad = [
        (loc, dep)
        for loc, dep in sources
        if "git+" in dep or " @ http" in dep or " @ file" in dep
    ]

    if bad:
        print("ERROR: direct URL dependencies are not allowed:")
        for loc, dep in bad:
            print(f"  [{loc}] {dep}")
        print()
        print("Use [tool.mcp-coder.install-from-github] for git installs.")
        return 1

    print("OK: no direct URL dependencies in [project]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
