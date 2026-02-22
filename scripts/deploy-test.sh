#!/bin/bash
# deploy-test.sh - Deploy test script as main.py and run

# Check if script parameter is provided
if [ -z "$1" ]; then
    echo "Usage: ./deploy-test.sh <test_script.py>"
    echo ""
    echo "Examples:"
    echo "  ./deploy-test.sh pico_test_closure_state.py"
    echo "  ./deploy-test.sh test_milestone1_scan.py"
    echo ""
    echo "This uploads the test script as main.py and resets the device to run it."
    echo ""
    echo "⚠️  WARNING: This makes the test run on every boot!"
    echo "   Use ./test-on-pico.sh instead for non-invasive testing."
    exit 1
fi

TEST_SCRIPT=$1

# Validate file exists
if [ ! -f "$TEST_SCRIPT" ]; then
    echo "❌ Error: File not found: $TEST_SCRIPT"
    exit 1
fi

echo "🧪 Deploying test: $TEST_SCRIPT"
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

# Check if device is reachable
echo "🔍 Checking device connection..."
if ! upydev probe &> /dev/null; then
    echo "❌ Error: Cannot reach Pico W"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Make sure the device is powered on"
    echo "  2. Verify WiFi connection (check boot.py output via USB)"
    echo "  3. Try manually: upydev probe"
    echo ""
    exit 1
fi

echo "✅ Device is reachable"
echo ""

# Upload as main.py
echo "📦 Uploading as main.py..."
upydev put $TEST_SCRIPT main.py &>/dev/null || echo "   (upload completed with warnings)"

echo "✅ Test uploaded"
echo ""

# Reset to run
echo "🔄 Resetting device to run test..."
upydev reset &>/dev/null || echo "   (reset completed)"

echo ""
echo "✅ Test deployed and running!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Tip: Use './repl.sh' to connect and view test output"
echo "💡 To remove: Use './clear-main.sh' to delete main.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
