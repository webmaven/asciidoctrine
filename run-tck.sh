#!/bin/bash
set -e

TCK_DIR="vendor/asciidoc-tck"

if [ ! -d "$TCK_DIR/node_modules" ]; then
    echo "Installing TCK dependencies..."
    (cd "$TCK_DIR" && npm ci)
fi

echo "Running TCK tests..."
node "$TCK_DIR/harness/bin/asciidoc-tck.js" cli --adapter-command "python3 bin/tck-adapter.py" || true
