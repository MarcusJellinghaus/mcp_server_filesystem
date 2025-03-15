"""Test cases for directory_utils module with problematic folders."""

import pytest
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from src.file_tools.directory_utils import filter_files_with_gitignore


def test_node_modules_pattern():
    """Test filtering with node_modules pattern - a common problematic folder."""
    spec = PathSpec.from_lines(GitWildMatchPattern, ["node_modules"])
    
    files = [
        "node_modules/package.json",  # Should be filtered
        "node_modules",               # Should be filtered (even without trailing slash)
        "some/path/node_modules/file.js",  # Should be filtered (nested node_modules)
        "nodemodules/file.txt",       # Should NOT be filtered (partial match)
        "myapp/src/components/Module.js"  # Should NOT be filtered
    ]
    
    filtered = filter_files_with_gitignore(files, spec)
    expected = ["nodemodules/file.txt", "myapp/src/components/Module.js"]
    
    assert set(filtered) == set(expected)


def test_path_with_trailing_slash():
    """Test patterns with trailing slash versus without trailing slash."""
    # Pattern with trailing slash should match only directories
    spec = PathSpec.from_lines(GitWildMatchPattern, ["build/"])
    
    files = [
        "build/output.txt",       # Should be filtered (in directory)
        "build",                  # Edge case - should be filtered (the directory itself)
        "build.txt",              # Should NOT be filtered (not a directory)
        "mybuild/file.txt",       # Should NOT be filtered (different directory)
        "some/path/build/file.js" # Should be filtered (nested 'build' directory)
    ]
    
    filtered = filter_files_with_gitignore(files, spec)
    expected = ["build.txt", "mybuild/file.txt"]
    
    assert set(filtered) == set(expected)


def test_partial_path_matches():
    """Test patterns that should not partially match folder names."""
    spec = PathSpec.from_lines(GitWildMatchPattern, ["/logs/"])
    
    files = [
        "logs/debug.log",         # Should be filtered (exact match)
        "logs",                   # Should be filtered (exact match)
        "mylogs/error.log",       # Should NOT be filtered (different folder)
        "system-logs/info.log",   # Should NOT be filtered (different folder)
        "some/path/logs/trace.log" # Should be filtered (nested 'logs' folder)
    ]
    
    filtered = filter_files_with_gitignore(files, spec)
    expected = ["mylogs/error.log", "system-logs/info.log"]
    
    assert set(filtered) == set(expected)


def test_nested_gitignore_patterns():
    """Test filtering with patterns that would occur in nested .gitignore files."""
    spec = PathSpec.from_lines(
        GitWildMatchPattern,
        [
            "*.log",           # Global pattern
            "build/",          # Global pattern
            "dist/coverage/**" # Project-specific pattern
        ]
    )
    
    files = [
        "app.log",                 # Should be filtered (matches *.log)
        "build/temp.txt",          # Should be filtered (in build/)
        "dist/coverage/report.html", # Should be filtered (matches dist/coverage/**)
        "dist/app.js",             # Should NOT be filtered (not in coverage)
        "docs/build/index.html"    # Should be filtered (matches build/)
    ]
    
    filtered = filter_files_with_gitignore(files, spec)
    expected = ["dist/app.js"]
    
    assert set(filtered) == set(expected)


def test_platform_specific_path_issues():
    """Test handling of paths with different separator styles."""
    spec = PathSpec.from_lines(GitWildMatchPattern, ["temp/"])
    
    files = [
        "temp/cache.txt",      # Unix-style path - should be filtered
        "temp\\debug.log",     # Windows-style path - should be filtered
        "my-temp/data.json"    # Should NOT be filtered (different directory)
    ]
    
    filtered = filter_files_with_gitignore(files, spec)
    expected = ["my-temp/data.json"]
    
    assert set(filtered) == set(expected)
