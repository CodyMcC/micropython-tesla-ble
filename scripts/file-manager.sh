#!/bin/bash
# file-manager.sh - Manage files on Pico W

# Deactivate venv if active to avoid conflicts with upydev
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate 2>/dev/null || true
fi

DEVICE=${1:-}
UPYDEV_CMD="upydev"

if [ -n "$DEVICE" ]; then
    UPYDEV_CMD="upydev --dev $DEVICE"
fi

show_menu() {
    echo ""
    echo "📁 Pico W File Manager"
    echo "======================"
    echo "1. List files (root)"
    echo "2. List files (/lib)"
    echo "3. List files (/proto)"
    echo "4. List files (/config)"
    echo "5. Delete file"
    echo "6. Download file"
    echo "7. Create directory"
    echo "8. Exit"
    echo ""
    read -p "Select option: " choice
    
    case $choice in
        1)
            echo ""
            echo "📂 Files in root directory:"
            $UPYDEV_CMD ls /
            ;;
        2)
            echo ""
            echo "📂 Files in /lib:"
            $UPYDEV_CMD ls /lib
            ;;
        3)
            echo ""
            echo "📂 Files in /proto:"
            $UPYDEV_CMD ls /proto
            ;;
        4)
            echo ""
            echo "📂 Files in /config:"
            $UPYDEV_CMD ls /config
            ;;
        5)
            echo ""
            read -p "File to delete (e.g., /main.py or /lib/test.py): " file
            if [ -n "$file" ]; then
                echo "🗑️  Deleting $file..."
                $UPYDEV_CMD rm $file
                echo "✅ File deleted"
            else
                echo "❌ No file specified"
            fi
            ;;
        6)
            echo ""
            read -p "Remote file path (e.g., /main.py): " remote
            read -p "Local destination path (e.g., ./backup.json): " local
            if [ -n "$remote" ] && [ -n "$local" ]; then
                echo "⬇️  Downloading $remote to $local..."
                $UPYDEV_CMD get $remote $local
                echo "✅ File downloaded"
            else
                echo "❌ Both paths are required"
            fi
            ;;
        7)
            echo ""
            read -p "Directory name (e.g., /data): " dir
            if [ -n "$dir" ]; then
                echo "📁 Creating directory $dir..."
                $UPYDEV_CMD mkdir $dir
                echo "✅ Directory created"
            else
                echo "❌ No directory name specified"
            fi
            ;;
        8)
            echo ""
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option"
            ;;
    esac
    
    show_menu
}

echo "🔌 Connecting to Pico W..."
if [ -n "$DEVICE" ]; then
    echo "📱 Using device: $DEVICE"
fi

# Check if upydev is installed
if ! command -v upydev &> /dev/null; then
    echo "❌ Error: upydev is not installed"
    echo "Install with: pip install upydev"
    exit 1
fi

# Check if device is reachable (single ping)
if ! ping -c 1 -W 5 192.168.1.169 &> /dev/null; then
    echo "❌ Error: Cannot reach Pico W at 192.168.1.169 (connection timeout)"
    echo "Make sure the device is powered on and connected to WiFi"
    echo "Check IP address with: upydev config"
    exit 1
fi

echo "✅ Connected to Pico W"

show_menu
