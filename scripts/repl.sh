#!/bin/bash
# repl.sh - Connect to Pico W REPL

DEVICE=${1:-}

# Deactivate venv if active to avoid conflicts with upydev
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate 2>/dev/null || true
fi

echo "🔌 Connecting to Pico W REPL..."
echo "💡 Press Ctrl+D to soft reset, Ctrl+C to interrupt, Ctrl+X to exit"
echo ""

if [ -n "$DEVICE" ]; then
    upydev --dev $DEVICE repl
else
    upydev repl
fi
