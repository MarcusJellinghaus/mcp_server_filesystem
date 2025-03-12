# MCP File System Server

A simple Model Context Protocol (MCP) server providing file system operations. This server offers a clean API for performing file system operations within a specified project directory, following the MCP protocol design.

## Features

- `list_directory`: List all files and directories in the project directory
- `read_file`: Read the contents of a file
- `write_file`: Write content to a file atomically

## Installation

```bash
# Clone the repository
git clone https://github.com/MarcusJellinghaus/mcp_server_filesystem.git
cd mcp-server-filesystem

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Server

```bash
python -m src.main --project-dir /path/to/project
```

The server uses FastMCP for operation. The project directory parameter (`--project-dir`) is **required** for security reasons. All file operations will be restricted to this directory. Attempts to access files outside this directory will result in an error.

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
                "C:\\path\\to\\your\\project"
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

4. Restart the Claude desktop app to apply changes

Claude will now be able to list, read, and write files in your specified project directory.

5. Log files location:
   - Windows: `%APPDATA%\Claude\logs`
   - These logs can be helpful for troubleshooting issues with the MCP server connection

For more information on logging and troubleshooting, see the [MCP Documentation](https://modelcontextprotocol.io/quickstart/user#getting-logs-from-claude-for-desktop).

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

### Write File
- Writes content to a file atomically
- Parameters:
  - `file_path` (string): Path to the file to write to (relative to project directory)
  - `content` (string): Content to write to the file
- Returns: Boolean indicating success

## Security Features

- All paths are normalized and validated to ensure they remain within the project directory
- Path traversal attacks are prevented
- Files are written atomically to prevent data corruption

## Project Structure

```
mcp_server_filesystem/
├── .gitignore             # Git ignore file
├── README.md              # Project documentation
├── PROJECT_STRUCTURE.md   # Detailed structure documentation
├── pyproject.toml         # Project configuration
├── requirements.txt       # Project dependencies
├── src/                   # Source code directory
│   ├── __init__.py        # Package initialization
│   ├── file_tools.py      # Implementation of file operations
│   ├── main.py            # Entry point to run the server
│   └── server.py          # FastMCP server implementation
└── tests/                 # Tests directory
    ├── __init__.py        # Test package initialization
    ├── test_file_tools.py # Tests for file operations
    ├── test_server.py     # Tests for API endpoints
    └── testdata/          # Test data directory
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/MarcusJellinghaus/mcp_server_filesystem.git
cd mcp-server-filesystem

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running with MCP Dev Tools

```bash
# Set the PYTHONPATH and run the server module using mcp dev
set PYTHONPATH=. && mcp dev src/server.py
```

## License

MIT

## Links

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
