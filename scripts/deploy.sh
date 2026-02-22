#!/bin/bash
# deploy.sh - Deploy full project to Pico W via WiFi
# Automatically cleans __pycache__ directories before deploying

echo "🚀 Tesla BLE Pico W Deployment"
echo "================================"
echo ""

# Step 1: Clean up __pycache__ directories locally
echo "🧹 Cleaning up __pycache__ directories..."
find lib -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find config -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Local cleanup complete"
echo ""

# Deactivate venv if active to avoid conflicts with upydev
if [ -n "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment detected, please run: deactivate"
    echo "   Then run this script again."
    exit 1
fi

# Check if upydev config exists
if [ ! -f "upydev_.config" ]; then
    echo "❌ Error: upydev_.config not found"
    echo ""
    echo "Please configure upydev first:"
    echo "  upydev config -t 192.168.1.169 -p <PASSWORD>"
    echo ""
    exit 1
fi

echo "📱 Using upydev configuration from upydev_.config"
echo ""

# Check if device is reachable
echo "🔍 Checking device connection..."
if ! upydev probe &> /dev/null; then
    echo "❌ Error: Cannot reach Pico W"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Make sure the device is powered on"
    echo "  2. Verify WiFi connection (check boot.py output via USB)"
    echo "  3. Try manually: upydev probe"
    echo "  4. Check if IP address changed in upydev_.config"
    echo ""
    exit 1
fi

echo "✅ Device is reachable"
echo ""

# Deploy lib/ directory (includes tesla_ble with proto inside)
# Note: proto/ is now inside lib/tesla_ble/proto/
# Note: boot.py and secrets.py are NEVER touched (WiFi config is user-managed)
if [ -d "lib" ]; then
    echo "📦 Deploying lib/ directory..."
    echo "   Syncing files..."
    upydev dsync lib /lib -fg <<< "y" 2>&1 | grep -v "^$" | grep -v "Traceback" | grep -v "File " | grep -v "TypeError" | head -20 || true
    echo "✅ lib/ deployed"
else
    echo "⚠️  Warning: lib/ directory not found, skipping"
fi
echo ""

# Deploy config/ directory
if [ -d "config" ]; then
    echo "📦 Deploying config/ directory..."
    upydev dsync config /config -fg <<< "y" 2>&1 | grep -v "^$" | grep -v "Traceback" | grep -v "File " | grep -v "TypeError" | head -10 || true
    echo "✅ config/ deployed"
else
    echo "⚠️  Warning: config/ directory not found, skipping"
fi
echo ""

# Deploy main.py if it exists
if [ -f "main.py" ]; then
    echo "📦 Deploying main.py..."
    upydev put main.py &>/dev/null || echo "   (upload completed with warnings)"
    echo "✅ main.py deployed"
else
    echo "ℹ️  No main.py found, skipping"
fi
echo ""

echo "✅ Deployment complete!"
echo "� Resetting device..."
echo ""

upydev reset &>/dev/null || echo "   (reset completed)"

echo "✨ Done! Your Pico W is running the updated code."
echo ""
echo "Next steps:"
echo "  • Use ./repl.sh to connect to REPL"
echo "  • Use ./test-on-pico.sh <script.py> to test without saving"
echo "  • Use ./deploy-test.sh <test.py> to deploy and run a test"
echo ""
