#!/bin/bash
set -e

TCK_DIR="vendor/asciidoc-tck"

if [ ! -d "$TCK_DIR/node_modules" ]; then
    echo "Installing TCK dependencies..."
    (cd "$TCK_DIR" && npm ci)
fi

# Determine coverage command (use venv if present, else global)
COVERAGE_CMD="coverage"
if [ -f "venv/bin/coverage" ]; then
    COVERAGE_CMD="venv/bin/coverage"
fi

echo "Running TCK tests with coverage..."
node "$TCK_DIR/harness/bin/asciidoc-tck.js" cli --adapter-command "PYTHONPATH=src $COVERAGE_CMD run --parallel-mode --source=src/asciidoctrine bin/tck-adapter.py" "$@"
