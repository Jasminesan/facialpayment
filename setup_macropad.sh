#!/bin/bash
# Setup script for MacroPad - enables USB CDC data port
# Run this on Raspberry Pi after plugging in MacroPad

set -e

MOUNT_POINT="/media/jasuminasan/CIRCUITPY"

echo "🔍 Checking for CIRCUITPY mount point..."

if [ ! -d "$MOUNT_POINT" ]; then
    echo "❌ CIRCUITPY not found at $MOUNT_POINT"
    echo "Please check if MacroPad is plugged in and mounted"
    exit 1
fi

echo "✅ Found CIRCUITPY at $MOUNT_POINT"

# Backup existing boot.py if present
if [ -f "$MOUNT_POINT/boot.py" ]; then
    echo "📦 Backing up existing boot.py to boot.py.backup"
    cp "$MOUNT_POINT/boot.py" "$MOUNT_POINT/boot.py.backup"
fi

# Create boot.py
echo "📝 Creating boot.py to enable CDC data port..."
cat > "$MOUNT_POINT/boot.py" << 'EOF'
# boot.py - Enable both console (REPL) and data (application) CDC ports
# This allows the MacroPad to send payment data via usb_cdc.data
# while keeping REPL available on usb_cdc.console
import usb_cdc
usb_cdc.enable(console=True, data=True)
EOF

sync
echo "✅ boot.py created successfully!"

# Copy the improved code.py if it doesn't exist
if [ ! -f "$MOUNT_POINT/code.py" ]; then
    echo "📝 Copying code.py from docs/macro_pad_code.py..."
    if [ -f "$(dirname "$0")/docs/macro_pad_code.py" ]; then
        cp "$(dirname "$0")/docs/macro_pad_code.py" "$MOUNT_POINT/code.py"
        sync
        echo "✅ code.py copied successfully!"
    else
        echo "⚠️  docs/macro_pad_code.py not found - please copy manually"
    fi
else
    echo "ℹ️  code.py already exists - not overwriting"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ MacroPad setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Next steps:"
echo "1. Unplug MacroPad from USB"
echo "2. Wait 2 seconds"
echo "3. Plug MacroPad back in (this will load the new boot.py)"
echo "4. Test with: python test_serial_read.py /dev/ttyACM0 115200"
echo "   Press MacroPad keys and you should see: 'PAY:100.00'"
echo "5. Run the app: python src/main.py"
echo ""
