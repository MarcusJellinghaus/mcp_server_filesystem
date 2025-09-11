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
- **Validation**: Alphanumeric + underscore/hyphen names, startup directory validation
- **Security**: Reuse existing path validation and security model
- **Error Handling**: Startup validation + runtime helpful messages
- **Consistency**: Follow existing patterns for naming, gitignore filtering, logging

## Technical Approach
- Extend CLI argument parsing in `main.py`
- Add global `_reference_projects: Dict[str, Path]` storage in `server.py`
- Reuse existing file operation utilities with new project_dir parameter
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
