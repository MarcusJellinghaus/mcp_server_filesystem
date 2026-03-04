#!/bin/bash
# Run import-linter architecture checks
set -e

echo "Running import-linter..."
lint-imports

echo ""
echo "✓ All import contracts satisfied!"
