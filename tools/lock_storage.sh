#!/bin/bash
# Script to safely lock secure storage

echo "======================================================================"
echo "                    SECURE STORAGE LOCK TOOL"
echo "======================================================================"
echo ""

# Mount point location
MOUNT_POINT="$HOME/SecureStorage"

# Check if storage is mounted
if mountpoint -q "$MOUNT_POINT" 2>/dev/null || [ -d "$MOUNT_POINT" ] && sudo veracrypt --text --list | grep -q "$MOUNT_POINT"; then
    echo "Step 1: Checking for open files..."

    # Check if any processes are using the mount
    OPEN_FILES=$(sudo lsof "$MOUNT_POINT" 2>/dev/null | tail -n +2)
    if [ -n "$OPEN_FILES" ]; then
        echo ""
        echo "⚠ WARNING: Files or programs are still using the secure storage!"
        echo ""
        echo "Open files/processes:"
        echo "$OPEN_FILES"
        echo ""
        echo "You should close these programs first to avoid data loss."
        echo ""
        read -p "Force close and lock anyway? (y/N): " FORCE
        if [ "$FORCE" != "y" ] && [ "$FORCE" != "Y" ]; then
            echo ""
            echo "Lock cancelled. Please:"
            echo "  1. Close all programs using the secure storage"
            echo "  2. Save any open documents"
            echo "  3. Run this script again"
            exit 1
        fi
        echo ""
        echo "Forcing lock (files will be closed)..."
    else
        echo "✓ No open files detected"
    fi

    echo ""
    echo "Step 2: Syncing pending writes to disk..."
    sync
    echo "✓ All data written to disk"

    echo ""
    echo "Step 3: Dismounting encrypted volume..."

    # Dismount the encrypted volume
    if sudo veracrypt --text --dismount "$MOUNT_POINT" 2>/dev/null; then
        rmdir "$MOUNT_POINT" 2>/dev/null
        echo "✓ Volume dismounted"
        echo ""
        echo "======================================================================"
        echo "                           SUCCESS!"
        echo "======================================================================"
        echo ""
        echo "Secure storage is now locked and encrypted."
        echo "Your data is safe to remove the device."
        echo ""
        echo "======================================================================"
    else
        echo ""
        echo "======================================================================"
        echo "                       DISMOUNT FAILED"
        echo "======================================================================"
        echo ""
        echo "Possible reasons:"
        echo "  • Files still in use (close all programs)"
        echo "  • Permission denied"
        echo "  • Volume not mounted with this script"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check what's using it: sudo lsof $MOUNT_POINT"
        echo "  2. Force dismount all: sudo veracrypt -d"
        echo "  3. Kill processes: sudo fuser -km $MOUNT_POINT"
        echo ""
        exit 1
    fi
else
    echo "ℹ Secure storage is not currently mounted."
    echo ""
    echo "Nothing to lock - your data is already secured."
    echo ""
    echo "If you want to access it, run:"
    echo "    sudo ./mount_storage.sh"
fi
