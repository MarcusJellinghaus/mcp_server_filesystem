#!/bin/bash
# Run all code quality and architecture checks
set -e

echo "========================================"
echo "Running All Code Quality Checks"
echo "========================================"
echo ""

echo "[1/7] Running black and isort..."
./tools/format_all.sh
echo ""

echo "[2/7] Running pylint..."
pylint ./src ./tests
echo ""

echo "[3/7] Running mypy..."
mypy --strict src tests
echo ""

echo "[4/7] Running pytest..."
pytest -n auto
echo ""

echo "========================================"
echo "Running Architecture Checks"
echo "========================================"
echo ""

echo "[5/7] Running import-linter..."
./tools/lint_imports.sh
echo ""

echo "[6/7] Running tach..."
./tools/tach_check.sh
echo ""

echo "[7/7] Running pycycle..."
./tools/pycycle_check.sh
echo ""

echo "========================================"
echo "✓ ALL CHECKS PASSED!"
echo "========================================"
