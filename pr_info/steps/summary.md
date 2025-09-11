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
- **Validation**: Alphanumeric + underscore/hyphen names, startup validation with warning logs for invalid references
- **Error Handling**: Reuse existing error handling patterns for consistency
- **Logging**: Include reference project context for better debugging
- **Utility Reuse**: Pass reference project path as project_dir parameter to existing utilities
- **Storage**: Simple global variable pattern for maximum simplicity
- **Startup Behavior**: Ignore invalid reference projects and continue with valid ones

## Technical Approach
- Extend CLI argument parsing in `main.py` for `--reference-project name=/path` format
- Add global `_reference_projects: Dict[str, Path]` storage in `server.py`
- Reuse existing file operation utilities by passing reference project path as project_dir parameter
- Convert reference project paths to absolute paths (same as main project)
- Validate at startup, log warnings for invalid references, continue with valid ones
- Follow same decorator patterns as existing MCP tools
- Maintain backward compatibility (no breaking changes)

## Files to Modify
- `src/mcp_server_filesystem/main.py` - CLI argument parsing
- `src/mcp_server_filesystem/server.py` - New tools and reference project management
- `README.md` - Documentation updates
- `tests/` - Test coverage for new functionality

## Benefits
- LLMs can reference multiple codebases for context
- Clean separation between main project (read/write) and references (read-only)
- Maintains security and follows established patterns
- Simple configuration and discovery mechanism
