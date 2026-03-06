#!/bin/bash
# Run pycycle circular dependency detection
set -e

echo "Running pycycle..."
pycycle --here

echo ""
echo "✓ No circular dependencies found!"
