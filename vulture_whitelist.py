"""
Vulture Whitelist - Intentionally Unused Code
==============================================
This file contains code patterns that vulture should not flag as unused.

Use this for:
- Public API methods that external users call
- Protocol-required methods (MCP server handlers)
- Callback functions registered dynamically
- __all__ exports that are imported elsewhere

Run: vulture src tests vulture_whitelist.py --min-confidence 60
"""

# =============================================================================
# MCP Server Tool Handlers
# =============================================================================
# These are registered dynamically by the MCP framework and called by clients.
# They appear unused but are part of the public MCP tool API.

# File operation tools registered in server.py
_.list_directory
_.read_file
_.save_file
_.append_file
_.delete_this_file
_.move_file
_.edit_file

_.search_files

# Reference project tools
_.get_reference_projects
_.list_reference_directory
_.read_reference_file

# =============================================================================
# Public API Exports
# =============================================================================
# Exported in __init__.py for external use

# Version information
_.__version__

# =============================================================================
# Test Fixtures and Utilities
# =============================================================================
# Pytest fixtures defined in conftest.py

_.temp_dir
_.temp_git_repo
_.sample_file
_.setup_and_cleanup
_.setup_test_file
_.setup_server

# =============================================================================
# Protocol-Required Attributes
# =============================================================================
# Attributes required by MCP protocol but may not be referenced in our code

_.name
_.description
_.inputSchema
