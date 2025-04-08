# Integrating MCP Server Filesystem with VSCode & Cline

This guide provides step-by-step instructions for integrating the MCP Server Filesystem with VSCode and the Cline extension, enabling Claude to interact with your local file system in a controlled manner.

## What is MCP Server Filesystem?

The MCP Server Filesystem is a Model Context Protocol (MCP) server that provides file system operations for AI assistants. It allows Claude to:

- Read existing code and project files
- Write new files with generated content
- Make selective edits to existing files
- Delete files when needed
- List directory contents

All operations are securely contained within your specified project directory, giving you control while enabling powerful AI collaboration on your local files.

## Prerequisites

- Python 3.13 or higher
- VSCode with the Cline extension installed
- Git (to clone the repository)

## Installation Steps

### 1. Clone and Install the MCP Server Filesystem

```bash
# Clone the repository
git clone https://github.com/MarcusJellinghaus/mcp_server_filesystem.git
cd mcp_server_filesystem

# Create and activate a virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# Install the project and dependencies
pip install -e .
```

### 2. Configure VSCode with Cline Extension

#### 2.1 Open VSCode Settings JSON

1. Open VSCode
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
3. Type "Preferences: Open Settings (JSON)" and select it

#### 2.2 Add MCP Server Configuration

Add the following configuration to your settings.json file:

```json
"saoudrizwan.claude-dev.mcpServers": {
  "filesystem": {
    "command": "C:\\path\\to\\mcp_server_filesystem\\.venv\\Scripts\\python.exe",
    "args": [
      "C:\\path\\to\\mcp_server_filesystem\\src\\main.py",
      "--project-dir",
      "${workspaceFolder}",
      "--log-level",
      "INFO"
    ],
    "env": {
      "PYTHONPATH": "C:\\path\\to\\mcp_server_filesystem\\"
    },
    "disabled": false,
    "autoApprove": []
  }
}
```

**Important Notes:**

- Replace `C:\\path\\to\\mcp_server_filesystem\\` with the actual path to where you cloned the repository
- On Windows, use double backslashes (`\\`) in paths
- On macOS/Linux, use forward slashes (`/`) instead
- The `${workspaceFolder}` variable will automatically use your current VSCode workspace as the project directory
- The `disabled: false` setting ensures the server is enabled by default
- The empty `autoApprove` array means all operations will require your approval

#### 2.3 Path Examples

**Windows Example:**
```json
"command": "C:\\Users\\YourUsername\\Documents\\GitHub\\mcp_server_filesystem\\.venv\\Scripts\\python.exe",
"args": [
  "C:\\Users\\YourUsername\\Documents\\GitHub\\mcp_server_filesystem\\src\\main.py",
  "--project-dir",
  "${workspaceFolder}",
  "--log-level",
  "INFO"
],
"env": {
  "PYTHONPATH": "C:\\Users\\YourUsername\\Documents\\GitHub\\mcp_server_filesystem\\"
}
```

**macOS/Linux Example:**
```json
"command": "/Users/YourUsername/Documents/GitHub/mcp_server_filesystem/.venv/bin/python",
"args": [
  "/Users/YourUsername/Documents/GitHub/mcp_server_filesystem/src/main.py",
  "--project-dir",
  "${workspaceFolder}",
  "--log-level",
  "INFO"
],
"env": {
  "PYTHONPATH": "/Users/YourUsername/Documents/GitHub/mcp_server_filesystem/"
}
```

### 3. Restart VSCode

After adding the configuration, restart VSCode to apply the changes.

### 4. Verify Integration

To verify the integration is working:

1. Open VSCode with a project folder
2. Open the Cline extension
3. Ask Claude to list files in your project directory:
   - "Can you list the files in my current project directory?"
4. Claude should be able to use the MCP server to list the files

## Available File Operations

Once integrated, you can ask Claude to perform various file operations:

1. **List files in a directory**:
   - "List all JavaScript files in the src directory"

2. **Read a file**:
   - "Show me the contents of src/main.js"

3. **Create a new file**:
   - "Create a new file called app.js with a basic React component"

4. **Edit an existing file**:
   - "Add error handling to the fetch function in src/api.js"

5. **Delete a file**:
   - "Delete the temporary.txt file"

## Advanced Configuration Options

### Custom Project Directory

If you want to specify a different project directory instead of using the current workspace:

```json
"args": [
  "C:\\path\\to\\mcp_server_filesystem\\src\\main.py",
  "--project-dir",
  "C:\\path\\to\\your\\specific\\project",
  "--log-level",
  "INFO"
]
```

### Logging Options

For more detailed logs:

```json
"args": [
  "C:\\path\\to\\mcp_server_filesystem\\src\\main.py",
  "--project-dir",
  "${workspaceFolder}",
  "--log-level",
  "DEBUG",
  "--log-file",
  "C:\\path\\to\\logs\\mcp_server_filesystem.json"
]
```

Available log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Auto-Approve Specific Operations

If you want to auto-approve certain operations without prompts:

```json
"autoApprove": ["list_directory", "read_file"]
```

This would automatically approve directory listing and file reading operations without prompting you.

## Troubleshooting

If you encounter issues with the integration:

### 1. Check Logs

- Windows: `%APPDATA%\Claude\logs` or `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\logs`
- macOS: `~/Library/Application Support/Claude/logs` or `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/logs`

### 2. Verify Paths

- Ensure all paths in the configuration are correct and use the proper format for your OS
- Check that the Python executable path points to the virtual environment you created

### 3. Check Permissions

- Make sure the specified project directory is accessible to the Python process
- Verify that the Python process has read/write permissions for the project directory

### 4. Test the Server Directly

Run the server manually to check for errors:

```bash
# Activate the virtual environment first
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Then run the server
python src/main.py --project-dir C:\path\to\your\project --log-level DEBUG
```

### 5. Common Errors

- **"Cannot connect to MCP server"**: Check that the paths in your configuration are correct and the server is properly installed
- **"Permission denied"**: Ensure the Python process has the necessary permissions to access the specified directories
- **"File not found"**: Verify that the file paths you're trying to access exist within the project directory

## Security Considerations

- All file operations are restricted to the specified project directory
- Path traversal attacks are prevented by the server
- Files are written atomically to prevent data corruption
- Delete operations are restricted to the project directory for safety

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Cline Extension Documentation](https://github.com/saoudrizwan/claude-dev)
- [MCP Server Filesystem GitHub Repository](https://github.com/MarcusJellinghaus/mcp_server_filesystem)
