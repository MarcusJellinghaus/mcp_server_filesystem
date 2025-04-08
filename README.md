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

## Integration Options

This server can be integrated with different Claude interfaces. Each requires a specific configuration.

## VSCode & Cline Extension Integration

The Cline extension for VSCode allows you to use Claude directly in your code editor. For more information about configuring MCP servers with Cline, see the [Cline MCP Servers documentation](https://docs.cline.bot/mcp-servers/configuring-mcp-servers).

### Configuration Steps for VSCode/Cline

1. **Locate the Cline MCP configuration file**:
   - Windows: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
   - macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

2. **Add the MCP server configuration** (create the file if it doesn't exist):

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "C:\\path\\to\\mcp_server_filesystem\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\mcp_server_filesystem\\src\\main.py",
        "--project-dir",
        "C:\\Users\\YourUsername\\Documents\\Projects\\MyProject",
        "--log-level",
        "INFO"
      ],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\mcp_server_filesystem\\"
      },
      "disabled": false,
      "autoApprove": [
        "list_directory",
        "read_file"
      ]
    }
  }
}
```

3. **Important VSCode/Cline-specific notes**:
   - Replace `${workspaceFolder}` with the actual full path to your project directory
   - Example: `"C:\\Users\\YourUsername\\Documents\\Projects\\MyProject"`
   - Replace all `C:\\path\\to\\` instances with your actual paths
   - Use double backslashes (`\\`) in paths on Windows, forward slashes (`/`) on macOS/Linux
   - The project directory should be the folder you want Claude to access
   - Only add operations to the `autoApprove` array that you want to be executed without requiring your approval each time
   - For better security, consider only auto-approving read-only operations like `list_directory` and `read_file`

4. **Restart VSCode** and test by asking Claude to "List the files in my current project directory"

### Troubleshooting VSCode/Cline Integration

- Check logs at: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\logs` (Windows) or `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/logs` (macOS)
- Verify the Python executable path points to your virtual environment
- Ensure all paths in your configuration are correct

## Claude Desktop App Integration

The Claude Desktop app can also use this file system server.

### Configuration Steps for Claude Desktop

1. **Locate the Claude Desktop configuration file**:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. **Add the MCP server configuration** (create the file if it doesn't exist):

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "C:\\path\\to\\mcp_server_filesystem\\.venv\\Scripts\\python.exe",
      "args": [                
        "C:\\path\\to\\mcp_server_filesystem\\src\\main.py",
        "--project-dir",
        "C:\\path\\to\\your\\specific\\project",
        "--log-level",
        "INFO"
      ],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\mcp_server_filesystem\\"
      },
      "disabled": false,
      "autoApprove": [
        "list_directory",
        "read_file"
      ]
    }
  }
}
```

3. **Important Claude Desktop-specific notes**:
   - You must specify an explicit project directory path in `--project-dir`
   - Replace all `C:\\path\\to\\` instances with your actual paths
   - The project directory should be the folder you want Claude to access
   - Only add operations to the `autoApprove` array that you want to be executed without requiring your approval each time
   - For better security, consider only auto-approving read-only operations like `list_directory` and `read_file`

4. **Restart the Claude Desktop app** to apply changes

### Troubleshooting Claude Desktop Integration

- Check logs at: `%APPDATA%\Claude\logs` (Windows) or `~/Library/Application Support/Claude/logs` (macOS)
- Ensure the specified project directory exists and is accessible
- Verify all paths in your configuration are correct

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

| Operation | Description | Example Prompt |
|-----------|-------------|----------------|
| `list_directory` | Lists files and directories in the project directory | "List all files in the src directory" |
| `read_file` | Reads the contents of a file | "Show me the contents of main.js" |
| `save_file` | Creates or overwrites files atomically | "Create a new file called app.js" |
| `append_file` | Adds content to existing files | "Add a function to utils.js" |
| `delete_this_file` | Removes files from the filesystem | "Delete the temporary.txt file" |
| `edit_file` | Makes selective edits using pattern matching | "Fix the bug in the fetch function" |

### Tool Details

#### List Directory
- Returns a list of file and directory names
- By default, results are filtered based on .gitignore patterns and .git folders are excluded

#### Read File
- Parameters: `file_path` (string): Path to the file to read (relative to project directory)
- Returns the content of the file as a string

#### Save File
- Parameters:
  - `file_path` (string): Path to the file to write to
  - `content` (string): Content to write to the file
- Returns a boolean indicating success

#### Append File
- Parameters:
  - `file_path` (string): Path to the file to append to
  - `content` (string): Content to append to the file
- Returns a boolean indicating success
- Note: The file must already exist; use `save_file` to create new files

#### Delete This File
- Parameters: `file_path` (string): Path to the file to delete
- Returns a boolean indicating success
- Note: This operation is irreversible and will permanently remove the file

#### Edit File
- Parameters:
  - `file_path` (string): File to edit
  - `edits` (array): List of edit operations, each containing:
    - `old_text` (string): Text to be replaced
    - `new_text` (string): Replacement text
  - `dry_run` (boolean, optional): Preview changes without applying
  - `options` (object, optional): Formatting settings
- Features:
  - Line-based and multi-line content matching
  - Whitespace normalization with indentation preservation
  - Multiple simultaneous edits with correct positioning
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

## Testing

The project includes pytest-based unit tests in the `tests/` directory. See [tests/README.md](tests/README.md) for details on test structure and execution.

For LLM-based testing, see [tests/LLM_Test.md](tests/LLM_Test.md). This file contains test instructions that can be directly pasted to an LLM to verify MCP server functionality.

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
- [Cline MCP Servers Documentation](https://docs.cline.bot/mcp-servers/configuring-mcp-servers)
- [Cline Extension for VSCode](https://github.com/saoudrizwan/claude-dev)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
