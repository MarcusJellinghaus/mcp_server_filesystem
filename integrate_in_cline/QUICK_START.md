# MCP Server Filesystem Quick Start Guide

This is a condensed guide for quickly integrating the MCP Server Filesystem with VSCode and Cline. For detailed instructions, see the [README.md](./README.md).

## 1. Install MCP Server Filesystem

```bash
# Clone and install
git clone https://github.com/MarcusJellinghaus/mcp_server_filesystem.git
cd mcp_server_filesystem
python -m venv .venv
.venv\Scripts\activate  # On Windows
pip install -e .
```

## 2. Configure VSCode

Add to VSCode settings.json (Ctrl+Shift+P → "Preferences: Open Settings (JSON)"):

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

Replace `C:\\path\\to\\mcp_server_filesystem\\` with your actual path.

## 3. Restart VSCode

Restart VSCode to apply the changes.

## 4. Test the Integration

Ask Claude in the Cline extension:
- "List the files in my current project directory"

## Available Operations

- **List files**: `list_directory`
- **Read file**: `read_file`
- **Write file**: `save_file`
- **Append to file**: `append_file`
- **Delete file**: `delete_this_file`
- **Edit file**: `edit_file` (selective edits with pattern matching)

## Troubleshooting

- Check logs in `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\logs` (Windows)
- Verify paths in your configuration
- Test the server directly: `python src/main.py --project-dir C:\path\to\project --log-level DEBUG`
