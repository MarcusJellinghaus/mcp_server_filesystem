#!/bin/bash
# Reinstall package in development mode
set -e

echo "Reinstalling mcp-workspace in development mode..."
pip install -e .

echo ""
echo "✓ Reinstall complete!"
echo ""
echo "To also install development dependencies, run:"
echo "pip install -e \".[dev]\""
