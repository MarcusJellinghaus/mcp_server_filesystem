#!/bin/bash
# Run tach architecture boundary checks
set -e

echo "Running tach..."
tach check

echo ""
echo "✓ All architectural boundaries respected!"
