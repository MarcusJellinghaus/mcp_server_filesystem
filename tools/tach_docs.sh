#!/usr/bin/env bash
# Generate architecture documentation (dependency graph and report)
#
# Creates:
#   - docs/architecture/dependency_graph.html
#   - docs/architecture/dependency_report.html

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python "$SCRIPT_DIR/tach_docs.py" "$@"
