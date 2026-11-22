#!/usr/bin/env bash
# ==============================================================================
# Sades Ryunix XR1 macOS — Interactive Web Diagnostic & Calibration Studio
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=8080

echo "🎮 ========================================================"
echo "   Sades Ryunix XR1 Web Diagnostic Studio"
echo "========================================================"
echo "📍 Server URL: http://localhost:${PORT}"
echo "🕹️  Connect your Sades Ryunix XR1 wheel via USB."
echo "🛑 Press Ctrl+C in this terminal to exit."
echo "========================================================"

if command -v open >/dev/null 2>&1; then
    (sleep 0.8 && open "http://localhost:${PORT}") &
fi

cd "${SCRIPT_DIR}/tester"
exec python3 server.py
