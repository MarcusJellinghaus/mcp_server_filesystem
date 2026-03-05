#!/bin/bash
# Run vulture dead code detection
set -e

echo "Running vulture..."
vulture src tests vulture_whitelist.py --min-confidence 60

echo ""
echo "✓ No dead code found!"
