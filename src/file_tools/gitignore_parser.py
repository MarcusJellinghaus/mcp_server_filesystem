"""Gitignore parser module.

This module provides compatibility with the gitignore_parser library
but uses PathSpec internally for better pattern matching.
"""

# Import our implementation from directory_utils
from .directory_utils import parse_gitignore
