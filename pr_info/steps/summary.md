# Reference Projects Implementation Summary

## Overview
Add support for multiple read-only reference projects to the MCP filesystem server. Users can configure one or more reference repositories/directories that the LLM can browse and read from, in addition to the main project directory.

## Core Features
- **Reference Project Configuration**: CLI argument `--reference-project name=/path/to/dir` (repeatable)
- **Read-only Access**: Three new MCP tools for reference project interaction
- **Discovery Mechanism**: LLM can discover available reference projects
- **Security**: Same path validation and gitignore filtering as main project

## New MCP Tools
1. `get_reference_projects() -> List[str]` - List available reference project names
2. `list_reference_directory(reference_name: str) -> List[str]` - List files in reference project
3. `read_reference_file(reference_name: str, file_path: str) -> str` - Read file from reference project

## Design Decisions
- **Read-only**: No write/edit/delete operations on reference projects
- **Path Handling**: Accept relative/absolute paths, convert to absolute internally (same as main project)
- **Validation**: Very permissive name validation (any non-empty string), startup validation with warning logs for invalid references
- **Duplicate Names**: Auto-rename with counter suffix (name_2, name_3, etc.)
- **Error Handling**: Exact replication of existing error handling patterns for consistency
- **Logging**: Mixed approach - INFO for discovery, DEBUG for file operations, include reference project context
- **Gitignore**: Always use gitignore filtering (use_gitignore=True)
- **Utility Reuse**: Pass reference project path as project_dir parameter to existing utilities
- **Storage**: Simple global variable pattern for maximum simplicity
- **Startup Behavior**: Warn for invalid reference projects and continue with valid ones only

## Technical Approach (TDD Implementation)
- **Test-Driven Development**: Write tests first for each step, then implement to pass tests
- Extend CLI argument parsing in `main.py` for `--reference-project name=/path` format
- Add global `_reference_projects: Dict[str, Path]` storage in `server.py`
- Reuse existing file operation utilities by passing reference project path as project_dir parameter
- Convert reference project paths to absolute paths (same as main project)
- Validate at startup, log warnings for invalid references, continue with valid ones
- Auto-rename duplicate reference project names with counter suffix
- Follow exact decorator patterns and error message patterns from existing MCP tools
- Target 15-20 focused tests across all functionality
- Maintain backward compatibility (no breaking changes)

## Files to Modify
- `tests/test_reference_projects.py` - **NEW FILE** - Comprehensive test coverage (TDD approach, ~15 focused tests)
- `src/mcp_server_filesystem/main.py` - CLI argument parsing
- `src/mcp_server_filesystem/server.py` - New tools and reference project management
- `README.md` - Documentation updates

## Benefits
- LLMs can reference multiple codebases for context
- Clean separation between main project (read/write) and references (read-only)
- Maintains security and follows established patterns
- Simple configuration and discovery mechanism
