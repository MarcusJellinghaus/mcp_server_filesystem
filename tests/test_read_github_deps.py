"""Tests for tools/read_github_deps.py."""

import textwrap
from pathlib import Path

import pytest

from tools.read_github_deps import main


def _write_pyproject(tmp_path: Path, content: str) -> None:
    (tmp_path / "pyproject.toml").write_text(textwrap.dedent(content))


def test_packages_generates_install_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Existing 'packages' key produces 'uv pip install "pkg"' lines."""
    _write_pyproject(
        tmp_path,
        """\
        [tool.mcp-coder.install-from-github]
        packages = ["pkg-a @ git+https://github.com/org/pkg-a.git"]
        """,
    )
    main(project_dir=tmp_path)
    out = capsys.readouterr().out
    assert 'uv pip install "pkg-a @ git+https://github.com/org/pkg-a.git"' in out


def test_packages_no_deps_generates_no_deps_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """'packages-no-deps' key produces 'uv pip install --no-deps "pkg"' lines."""
    _write_pyproject(
        tmp_path,
        """\
        [tool.mcp-coder.install-from-github]
        packages-no-deps = ["pkg-b @ git+https://github.com/org/pkg-b.git"]
        """,
    )
    main(project_dir=tmp_path)
    out = capsys.readouterr().out
    assert (
        'uv pip install --no-deps "pkg-b @ git+https://github.com/org/pkg-b.git"' in out
    )


def test_both_packages_and_no_deps(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Both keys produce correct commands (packages first, then no-deps)."""
    _write_pyproject(
        tmp_path,
        """\
        [tool.mcp-coder.install-from-github]
        packages = ["pkg-a @ git+https://github.com/org/pkg-a.git"]
        packages-no-deps = ["pkg-b @ git+https://github.com/org/pkg-b.git"]
        """,
    )
    main(project_dir=tmp_path)
    out = capsys.readouterr().out
    lines = out.strip().splitlines()
    assert len(lines) == 2
    assert 'uv pip install "pkg-a @ git+https://github.com/org/pkg-a.git"' in lines[0]
    assert (
        'uv pip install --no-deps "pkg-b @ git+https://github.com/org/pkg-b.git"'
        in lines[1]
    )


def test_missing_pyproject_returns_silently(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When pyproject.toml doesn't exist, no output, no error."""
    main(project_dir=tmp_path)
    out = capsys.readouterr().out
    assert out == ""


def test_empty_config_returns_silently(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When install-from-github section is absent, no output."""
    _write_pyproject(
        tmp_path,
        """\
        [tool.mcp-coder]
        name = "test"
        """,
    )
    main(project_dir=tmp_path)
    out = capsys.readouterr().out
    assert out == ""


def test_multiple_packages_grouped_in_one_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Multiple 'packages' entries are joined into a single install command."""
    _write_pyproject(
        tmp_path,
        """\
        [tool.mcp-coder.install-from-github]
        packages = ["pkg-a @ git+https://github.com/org/pkg-a.git", "pkg-b @ git+https://github.com/org/pkg-b.git"]
        """,
    )
    main(project_dir=tmp_path)
    out = capsys.readouterr().out
    lines = out.strip().splitlines()
    assert len(lines) == 1
    assert '"pkg-a @ git+https://github.com/org/pkg-a.git"' in lines[0]
    assert '"pkg-b @ git+https://github.com/org/pkg-b.git"' in lines[0]
