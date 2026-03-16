# This file makes the mcp_workspace directory a Python package

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mcp-workspace")
except PackageNotFoundError:
    # Package is not installed
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
