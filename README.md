# MCP File System Server

A simple Model Context Protocol (MCP) server providing file system operations. This server offers a clean API for performing file system operations within a specified project directory, following the MCP protocol design.

## Overview

This MCP server enables AI assistants like Claude (via Claude Desktop) or other MCP-compatible systems to interact with your local file system. With these capabilities, AI assistants can:

- Read your existing code and project files
- Write new files with generated content
- Update and modify existing files with precision using exact string matching
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
- `edit_file`: Make selective edits using exact string matching
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

Once installed, you can use the `mcp-server-filesystem` command directly:

```bash
mcp-server-filesystem --project-dir /path/to/project [--log-level LEVEL] [--log-file PATH]
```

### Command Line Arguments:

- `--project-dir`: (Required) Directory to serve files from
- `--log-level`: (Optional) Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-file`: (Optional) Path for structured JSON logs. If not specified, logs to mcp_filesystem_server_{timestamp}.log in project_dir/logs/.

The server uses FastMCP for operation. The project directory parameter (`--project-dir`) is **required** for security reasons. All file operations will be restricted to this directory. Attempts to access files outside this directory will result in an error.

## Structured Logging

The server provides flexible logging options:

- Standard human-readable logs to console
- Structured JSON logs to file (default: `project_dir/logs/mcp_filesystem_server_{timestamp}.log` or custom path with `--log-file`)
- Function call tracking with parameters, timing, and results
- Automatic error context capture
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Use `--console-only` to disable file logging

## Integration Options

This server can be integrated with different Claude interfaces. Each requires a specific configuration.

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
      "command": "mcp-server-filesystem",
      "args": [
        "--project-dir",
        "C:\\path\\to\\your\\specific\\project",
        "--log-level",
        "INFO"
      ]
    }
  }
}
```

3. **Configuration notes**:
   - The `mcp-server-filesystem` command should be available in your PATH after installation
   - You must specify an explicit project directory path in `--project-dir`
   - Replace the project directory path with your actual project path
   - The project directory should be the folder you want Claude to access

4. **Restart the Claude Desktop app** to apply changes

### Troubleshooting Claude Desktop Integration

- Check logs at: `%APPDATA%\Claude\logs` (Windows) or `~/Library/Application Support/Claude/logs` (macOS)
- Verify the `mcp-server-filesystem` command is available in your PATH (run `mcp-server-filesystem --help` to test)
- Ensure the specified project directory exists and is accessible
- Verify all paths in your configuration are correct

## Contributing

For development setup, testing, and contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Available Tools

The server exposes the following MCP tools:

| Operation | Description | Example Prompt |
|-----------|-------------|----------------|
| `list_directory` | Lists files and directories in the project directory | "List all files in the src directory" |
| `read_file` | Reads the contents of a file | "Show me the contents of main.js" |
| `save_file` | Creates or overwrites files atomically | "Create a new file called app.js" |
| `append_file` | Adds content to existing files | "Add a function to utils.js" |
| `delete_this_file` | Removes files from the filesystem | "Delete the temporary.txt file" |
| `edit_file` | Makes selective edits using exact string matching | "Fix the bug in the fetch function" |

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
Makes precise edits to files using exact string matching. This tool is designed for reliability and predictability.

**Parameters:**
- `file_path` (string): File to edit (relative to project directory)
- `edits` (array): List of edit operations, each containing:
  - `old_text` (string): Exact text to find and replace (must match exactly)
  - `new_text` (string): Replacement text
- `dry_run` (boolean, optional): Preview changes without applying (default: False)
- `options` (object, optional): Formatting settings
  - `preserve_indentation` (boolean, default: False): Apply indentation from old_text to new_text

**Key Characteristics:**
- **Exact string matching only** - The `old_text` must match exactly (case-sensitive, whitespace-sensitive)
- **No fuzzy or partial matching** - For maximum reliability and predictability
- **First occurrence replacement** - Only replaces the first match of each `old_text` pattern
- **Sequential processing** - Edits are applied in order, with each edit seeing the results of previous edits
- **Already-applied detection** - Automatically detects when edits are already applied (no-op optimization)
- **Git-style diff output** - Shows exactly what changed in unified diff format
- **Clear error reporting** - Specific messages when text patterns are not found

**Examples:**
```python
# Basic text replacement
edit_file("config.py", [
    {"old_text": "DEBUG = False", "new_text": "DEBUG = True"}
])

# Multiple edits in one operation
edit_file("app.py", [
    {"old_text": "def old_function():", "new_text": "def new_function():"},
    {"old_text": "old_function()", "new_text": "new_function()"}
])

# Preview changes without applying
edit_file("code.py", edits, dry_run=True)

# With indentation preservation
edit_file("indented.py", [
    {"old_text": "    old_code()", "new_text": "new_code()"}
], options={"preserve_indentation": True})
```

**Important Notes:**
- The text in `old_text` must match exactly - including spacing, capitalization, and line breaks
- Use `\n` for line breaks in multi-line replacements
- If `old_text` appears multiple times, only the first occurrence is replaced
- Consider using `dry_run=True` to preview changes before applying them

## Security Features

- All paths are normalized and validated to ensure they remain within the project directory
- Path traversal attacks are prevented
- Files are written atomically to prevent data corruption
- Delete operations are restricted to the project directory for safety

### MCP Configuration Management Tool

For easy configuration and installation of this MCP server, you can use the **mcp-config** development tool. This CLI tool simplifies the process of managing MCP server configurations across multiple clients (Claude Desktop, VS Code, etc.).

#### Installation

```bash
# Install mcp-config
pip install git+https://github.com/MarcusJellinghaus/mcp-config.git
```

#### Quick Setup

```bash
# Setup for Claude Desktop with automatic configuration
mcp-config setup mcp-server-filesystem "Filesystem Server" --project-dir /path/to/your/project

# Setup with custom log configuration
mcp-config setup mcp-server-filesystem "Filesystem Server" \
  --project-dir /path/to/your/project \
  --log-level DEBUG \
  --log-file /custom/path/server.log
```

**Learn more:** [mcp-config on GitHub](https://github.com/MarcusJellinghaus/mcp-config)

This tool eliminates the manual configuration steps and reduces setup errors by handling path resolution, environment detection, and client-specific configuration formats automatically.



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License is a permissive license that allows reuse with minimal restrictions. It permits use, copying, modification, and distribution with proper attribution.

## Links

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Python Code Checker](https://github.com/MarcusJellinghaus/mcp_server_code_checker_python)
- [MCP Configuration Tool](https://github.com/MarcusJellinghaus/mcp-config)
- [Cline MCP Servers Documentation](https://docs.cline.bot/mcp-servers/configuring-mcp-servers)
- [Cline Extension for VSCode](https://github.com/saoudrizwan/claude-dev)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
