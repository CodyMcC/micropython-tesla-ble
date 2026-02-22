#!/bin/bash
# Test script on Pico without deploying as main.py
# Usage: ./test-on-pico.sh script.py

set -e

SCRIPT="$1"

if [ -z "$SCRIPT" ]; then
    echo "Usage: ./test-on-pico.sh <script.py>"
    exit 1
fi

if [ ! -f "$SCRIPT" ]; then
    echo "Error: Script '$SCRIPT' not found"
    exit 1
fi

# Deactivate venv if active to avoid conflicts with upydev
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate 2>/dev/null || true
fi

echo "🧪 Running test: $SCRIPT"
echo ""

# Upload script to device first (required for upydev run to work)
upydev put "$SCRIPT" "/$SCRIPT" > /dev/null 2>&1

# Run the script
upydev run "$SCRIPT"

# Clean up (optional - files in root are harmless)
upydev cmd "import uos; uos.remove('/$SCRIPT')" > /dev/null 2>&1 || true
