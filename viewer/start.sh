#!/usr/bin/env bash
# Foolproof launcher for the Research Portal.
# Usage:  ./start.sh         (from inside the viewer/ directory)
#
# It checks Node, installs dependencies the first time, then starts the
# dev server and prints the URL to open in your browser.

set -euo pipefail
cd "$(dirname "$0")"

PORT=3333

# 1. Require Node.js 18+
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js is not installed. Install Node 18+ from https://nodejs.org and re-run." >&2
  exit 1
fi
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$NODE_MAJOR" -lt 18 ]; then
  echo "ERROR: Node $(node -v) is too old. This app needs Node 18 or newer." >&2
  exit 1
fi

# 2. Install dependencies on first run (or if they're missing)
if [ ! -d node_modules ]; then
  echo "==> First run: installing dependencies (this takes ~30s)..."
  npm install
fi

# 3. Start the server
echo ""
echo "==> Starting the Research Portal..."
echo "==> When it says 'Ready', open this in your browser:"
echo ""
echo "        http://localhost:${PORT}"
echo ""
exec npm run dev
