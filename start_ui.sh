#!/usr/bin/env bash
# UrivDocs — Start frontend only
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/ui"

if [[ ! -d "node_modules" ]]; then
    echo "▶ Installing npm packages..."
    npm install
fi

echo "▶ Starting React frontend..."
echo ""
echo "  🌐  App → http://localhost:5173"
echo ""
npm run dev -- --port 5173
