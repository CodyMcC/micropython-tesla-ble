#!/bin/bash
# Remove main.py from Pico to prevent auto-run on boot

set -e

# Deactivate venv if active to avoid conflicts with upydev
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate 2>/dev/null || true
fi

echo "🧹 Clearing main.py from Pico..."
echo ""

# Wait for device to be responsive
echo "Checking device..."
upydev probe

echo ""
echo "Removing main.py..."

# Remove main.py using raw command
upydev cmd "
try:
    import uos
    uos.remove('/main.py')
    print('✓ main.py removed')
except OSError:
    print('✓ main.py does not exist')
"

echo ""
echo "✅ Done! Pico will boot to REPL without running any script."
