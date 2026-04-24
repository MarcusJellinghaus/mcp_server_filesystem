"""Tree-based directory listing with collapsing and truncation.

Builds a tree from flat file paths, supports auto-collapsing of large
directories, and renders back to a flat list of path strings.
"""

from dataclasses import dataclass, field
from typing import Dict, List

_COLLAPSE_THRESHOLD = 250


@dataclass
class _TreeNode:
    """Internal tree node representing a directory."""

    name: str
    children: Dict[str, "_TreeNode"] = field(default_factory=dict)
    files: List[str] = field(default_factory=list)
    collapsed: bool = False
    collapsed_file_count: int = 0


def _build_tree(file_paths: List[str], base_path: str) -> _TreeNode:
    """Build tree from flat file paths.

    Args:
        file_paths: List of project-relative file paths.
        base_path: Path prefix to strip from each path for tree building.

    Returns:
        Root tree node.
    """
    root = _TreeNode(name="")
    strip_prefix = ""
    if base_path not in (".", ""):
        strip_prefix = base_path.rstrip("/") + "/"

    for file_path in file_paths:
        # Strip base_path prefix for tree building
        rel_path = file_path
        if strip_prefix and file_path.startswith(strip_prefix):
            rel_path = file_path[len(strip_prefix) :]

        parts = rel_path.split("/")
        node = root

        # Walk/create directory nodes for all parts except the last (filename)
        for dir_part in parts[:-1]:
            if dir_part not in node.children:
                node.children[dir_part] = _TreeNode(name=dir_part)
            node = node.children[dir_part]

        # Add filename to leaf node
        node.files.append(parts[-1])

    return root


def _render(node: _TreeNode, prefix: str, dirs_only: bool) -> List[str]:
    """Render tree to flat list of path strings.

    Args:
        node: Tree node to render.
        prefix: Path prefix to prepend (includes base_path for project-relative output).
        dirs_only: If True, only include directory entries (not files).

    Returns:
        List of rendered path strings.
    """
    results: List[str] = []

    for child_name in sorted(node.children):
        child_node = node.children[child_name]
        child_prefix = prefix + child_name + "/"
        if dirs_only:
            results.append(child_prefix)
        results.extend(_render(child_node, child_prefix, dirs_only))

    if not dirs_only:
        for filename in sorted(node.files):
            results.append(prefix + filename)

    return results


def list_directory_tree(
    file_paths: List[str],
    base_path: str = ".",
    dirs_only: bool = False,
) -> List[str]:
    """Build tree from file paths and render back to flat list.

    Public API: build tree, render to list.
    Collapsing and truncation will be added in later steps.

    Args:
        file_paths: List of project-relative file paths.
        base_path: Base path for scoping (stripped internally, re-added in output).
        dirs_only: If True, only return directory entries.

    Returns:
        List of project-relative path strings.
    """
    if not file_paths:
        return []

    tree = _build_tree(file_paths, base_path)
    render_prefix = ""
    if base_path not in (".", ""):
        render_prefix = base_path.rstrip("/") + "/"
    return _render(tree, prefix=render_prefix, dirs_only=dirs_only)
