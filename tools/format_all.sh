#!/bin/bash
# Format all Python code with black and isort
set -e

echo "Running isort..."
isort --profile=black --float-to-top src tests

echo "Running black..."
black src tests

echo ""
echo "✓ Formatting complete!"
