#!/bin/bash
# Local launcher for Claude Code with MCP servers using active environment
# Assumes mcp-coder is installed in currently active virtual environment
set -e

# Check if local .venv exists
if [ ! -f ".venv/bin/activate" ]; then
    echo "ERROR: Local virtual environment not found at .venv"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'"
    exit 1
fi

# Get expected virtual environment path
EXPECTED_VENV="$(pwd)/.venv"

# Check if wrong virtual environment is activated
if [ -n "$VIRTUAL_ENV" ] && [ "$VIRTUAL_ENV" != "$EXPECTED_VENV" ]; then
    echo "INFO: Deactivating wrong virtual environment"
    echo "  Current: $VIRTUAL_ENV"
    echo "  Expected: $EXPECTED_VENV"
    deactivate 2>/dev/null || true
    unset VIRTUAL_ENV
fi

# Activate correct virtual environment if needed
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating local virtual environment..."
    source .venv/bin/activate
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "ERROR: Failed to activate virtual environment"
        echo "Please check .venv/bin/activate"
        exit 1
    fi
fi

# Check if mcp-coder is available in the local environment
if ! python -c "import mcp_coder" 2>/dev/null; then
    echo "ERROR: mcp-coder not found in local virtual environment"
    echo "Local environment: $VIRTUAL_ENV"
    echo "Please run: pip install git+https://github.com/MarcusJellinghaus/mcp_coder.git"
    exit 1
fi

# Set project directories for MCP servers
export MCP_CODER_PROJECT_DIR="$(pwd)"
export MCP_CODER_VENV_DIR="$(pwd)/.venv"
export DISABLE_AUTOUPDATER=1

# Start Claude Code using the local mcp-coder installation
echo "Starting Claude Code with:"
echo "VIRTUAL_ENV=$VIRTUAL_ENV"
echo "MCP_CODER_PROJECT_DIR=$MCP_CODER_PROJECT_DIR"
echo "MCP_CODER_VENV_DIR=$MCP_CODER_VENV_DIR"
echo "DISABLE_AUTOUPDATER=$DISABLE_AUTOUPDATER"

# Try to find claude executable
if command -v claude &> /dev/null; then
    claude "$@"
elif [ -f "$HOME/.local/bin/claude" ]; then
    "$HOME/.local/bin/claude" "$@"
else
    echo "ERROR: claude executable not found"
    echo "Please install Claude Code: https://claude.ai/download"
    exit 1
fi
