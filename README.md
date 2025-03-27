# MCP File System Server

A simple Model Context Protocol (MCP) server providing file system operations. This server offers a clean API for performing file system operations within a specified project directory, following the MCP protocol design.

## Overview

This MCP server enables AI assistants like Claude (via Claude Desktop) or other MCP-compatible systems to interact with your local file system. With these capabilities, AI assistants can:

- Read your existing code and project files
- Write new files with generated content
- Update and modify existing files with precision using pattern matching
- Make selective edits to code without rewriting entire files
- Delete files when needed
- Review repositories to provide analysis and recommendations
- Debug and fix issues in your codebase
- Generate complete implementations based on your specifications

All operations are securely contained within your specified project directory, giving you control while enabling powerful AI collaboration on your local files.

By connecting your AI assistant to your filesystem, you can transform your workflow from manual coding to a more intuitive prompting approach - describe what you need in natural language and let the AI generate, modify, and organize code directly in your project files.

## Features

- `list_directory`: List all files and directories in the project directory
- `read_file`: Read the contents of a file
- `save_file`: Write content to a file atomically
- `append_file`: Append content to the end of a file
- `delete_this_file`: Delete a specified file from the filesystem
- `edit_file`: Make selective edits using advanced pattern matching
- `Structured Logging`: Comprehensive logging system with both human-readable and JSON formats

## Installation

```bash
# Clone the repository
git clone https://github.com/MarcusJellinghaus/mcp_server_filesystem.git
cd mcp-server-filesystem

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies using pip with pyproject.toml
pip install -e .
```

## Running the Server

```bash
python -m src.main --project-dir /path/to/project [--log-level LEVEL] [--log-file PATH]
```

Alternatively, you can add the current directory to your PYTHONPATH and run the script directly:

```cmd
set PYTHONPATH=%PYTHONPATH%;.
python .\src\main.py --project-dir /path/to/project [--log-level LEVEL] [--log-file PATH]
```

### Command Line Arguments:

- `--project-dir`: (Required) Directory to serve files from
- `--log-level`: (Optional) Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-file`: (Optional) Path for structured JSON logs. If not specified, only console logging is used.

The server uses FastMCP for operation. The project directory parameter (`--project-dir`) is **required** for security reasons. All file operations will be restricted to this directory. Attempts to access files outside this directory will result in an error.

## Structured Logging

The server provides flexible logging options:

- Standard human-readable logs to console
- Optional structured JSON logs to file with `--log-file`
- Function call tracking with parameters, timing, and results
- Automatic error context capture
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Using with Claude Desktop App

To enable Claude to use this file system server for accessing files in your local environment:

1. Create or modify the Claude configuration file:
   - Location: `%APPDATA%\Claude\claude_desktop_config.json` (on Windows)
   - On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add the MCP server configuration to the file:

```json
{
    "mcpServers": {
        "basic_filesystem": {
            "command": "C:\\path\\to\\mcp_server_filesystem\\.venv\\Scripts\\python.exe",
            "args": [                
                "C:\\path\\to\\mcp_server_filesystem\\src\\main.py",
                "--project-dir",
                "C:\\path\\to\\your\\project",
                "--log-level",
                "INFO",
                "--log-file",
                "C:\\path\\to\\logs\\mcp_server_filesystem_structured.log"
            ],
            "env": {
                "PYTHONPATH": "C:\\path\\to\\mcp_server_filesystem\\"
            }
        }
    }
}
```

3. Replace all `C:\\path\\to\\` instances with your actual paths:
   - Point to your Python virtual environment 
   - Set the project directory to the folder you want Claude to access
   - Make sure the PYTHONPATH points to the mcp_server_filesystem root folder
   - Specify log level and log file path as needed

4. Restart the Claude desktop app to apply changes

Claude will now be able to list, read, write, and delete files in your specified project directory.

5. Log files location:
   - Windows: `%APPDATA%\Claude\logs`
   - These logs can be helpful for troubleshooting issues with the MCP server connection

For more information on logging and troubleshooting, see the [MCP Documentation](https://modelcontextprotocol.io/quickstart/user#getting-logs-from-claude-for-desktop).

## Using MCP Inspector

MCP Inspector allows you to debug and test your MCP server:

1. Start MCP Inspector by running:

```bash
npx @modelcontextprotocol/inspector \
  uv \
  --directory C:\path\to\mcp_server_filesystem \
  run \
  src\main.py
```

2. In the MCP Inspector web UI, configure with the following:
   - Python interpreter: `C:\path\to\mcp_server_filesystem\.venv\Scripts\python.exe`
   - Arguments: `C:\path\to\mcp_server_filesystem\src\main.py --project-dir C:\path\to\your\project --log-level DEBUG`
   - Environment variables:
     - Name: `PYTHONPATH`
     - Value: `C:\path\to\mcp_server_filesystem\`

3. This will launch the server and provide a debug interface for testing the available tools.

## Available Tools

The server exposes the following MCP tools:

### List Directory
- Lists all files and directories in the project directory
- Returns: List of file and directory names
- By default, results are filtered based on .gitignore patterns and .git folders are excluded

### Read File
- Reads the contents of a file
- Parameters:
  - `file_path` (string): Path to the file to read (relative to project directory)
- Returns: Content of the file as a string

### Save File
- Writes content to a file atomically
- Parameters:
  - `file_path` (string): Path to the file to write to (relative to project directory)
  - `content` (string): Content to write to the file
- Returns: Boolean indicating success

### Append File
- Appends content to the end of an existing file
- Parameters:
  - `file_path` (string): Path to the file to append to (relative to project directory)
  - `content` (string): Content to append to the file
- Returns: Boolean indicating success
- Note: The file must already exist; use `save_file` to create new files

### Delete This File
- Deletes a specified file from the filesystem
- Parameters:
  - `file_path` (string): Path to the file to delete (relative to project directory)
- Returns: Boolean indicating success
- Note: This operation is irreversible and will permanently remove the file. Only works within allowed directories.

### Edit File
- Makes selective edits using advanced pattern matching and formatting
- Parameters:
  - `path` (string): File to edit (relative to project directory)
  - `edits` (array): List of edit operations, each containing:
    - `old_text` (string): Text to be replaced (must be unique in the file)
    - `new_text` (string): Replacement text
  - `dry_run` (boolean, optional): Preview changes without applying (default: False)
  - `options` (object, optional): Formatting settings:
    - `preserveIndentation` (boolean): Keep existing indentation (default: True)
    - `normalizeWhitespace` (boolean): Normalize spaces while preserving structure (default: True)
    - `partialMatch` (boolean): Enable fuzzy matching (default: True)
    - `matchThreshold` (float): Confidence threshold for fuzzy matching (default: 0.8)
- Returns: Detailed diff and match information
- Features:
  - Line-based and multi-line content matching
  - Whitespace normalization with indentation preservation
  - Fuzzy matching with confidence scoring
  - Multiple simultaneous edits with correct positioning
  - Indentation style detection and preservation
  - Git-style diff output with context

## Security Features

- All paths are normalized and validated to ensure they remain within the project directory
- Path traversal attacks are prevented
- Files are written atomically to prevent data corruption
- Delete operations are restricted to the project directory for safety

## Development

### Setting up the development environment on windows

```cmd
REM Clone the repository
git clone https://github.com/MarcusJellinghaus/mcp_server_filesystem.git
cd mcp-server-filesystem

REM Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

REM Install dependencies
pip install -e .

REM Install development dependencies
pip install -e ".[dev]"

```

## Running with MCP Dev Tools

```bash
# Set the PYTHONPATH and run the server module using mcp dev
set PYTHONPATH=. && mcp dev src/server.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License is a permissive license that allows reuse with minimal restrictions. It permits use, copying, modification, and distribution with proper attribution.

## Links

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Python Code Checker](https://github.com/MarcusJellinghaus/mcp_server_code_checker_python)
