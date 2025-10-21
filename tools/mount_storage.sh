#!/bin/bash
# Script to mount secure storage partition

echo "======================================================================"
echo "                    SECURE STORAGE MOUNT TOOL"
echo "======================================================================"
echo ""

# Function to find the documents partition (second-to-last partition on drive)
find_docs_partition() {
    # Look for drives with TOOLS partition (our indicator)
    local tools_drive=$(lsblk -ln -o NAME,LABEL | grep "TOOLS" | awk '{print $1}' | head -1)

    if [ -z "$tools_drive" ]; then
        echo "ERROR: Could not find TOOLS partition."
        echo "Please ensure the secure storage device is connected."
        return 1
    fi

    # Get the base drive name (remove partition number)
    local base_drive=$(echo "$tools_drive" | sed 's/[0-9]*$//' | sed 's/p$//')

    # Get all partitions on this drive
    local partitions=$(lsblk -ln -o NAME "/dev/$base_drive" | grep "^$base_drive" | tail -n +2)
    local part_count=$(echo "$partitions" | wc -l)

    if [ "$part_count" -lt 2 ]; then
        echo "ERROR: Not enough partitions found."
        return 1
    fi

    # Get second-to-last partition (documents partition)
    local docs_part=$(echo "$partitions" | tail -n 2 | head -n 1)
    echo "/dev/$docs_part"
    return 0
}

echo "Step 1: Detecting secure storage device..."
DOCS_PARTITION=$(find_docs_partition)

if [ $? -ne 0 ]; then
    echo ""
    echo "======================================================================"
    echo "AUTO-DETECTION FAILED - MANUAL MODE"
    echo "======================================================================"
    echo ""
    echo "Available partitions:"
    lsblk -o NAME,SIZE,TYPE,LABEL,FSTYPE | grep -v "loop"
    echo ""
    echo "TIP: Look for a partition WITHOUT a filesystem (blank FSTYPE)"
    echo "      This is usually your encrypted documents partition."
    echo ""
    read -p "Enter the partition path (e.g., /dev/sdb1): " DOCS_PARTITION

    if [ -z "$DOCS_PARTITION" ]; then
        echo "ERROR: No partition specified."
        exit 1
    fi

    if [ ! -b "$DOCS_PARTITION" ]; then
        echo "ERROR: $DOCS_PARTITION is not a valid block device."
        exit 1
    fi
fi

echo "✓ Found encrypted partition: $DOCS_PARTITION"
echo ""

echo "Step 2: Creating mount point..."
# Mount in user's home directory for easy access
MOUNT_POINT="$HOME/SecureStorage"
mkdir -p "$MOUNT_POINT"
echo "✓ Mount point ready at: $MOUNT_POINT"
echo ""

echo "Step 3: Mounting encrypted volume..."
echo "You will now be prompted for your encryption password."
echo ""

# Mount the encrypted volume
if sudo veracrypt --text --mount "$DOCS_PARTITION" "$MOUNT_POINT"; then
    echo ""
    echo "Setting correct permissions..."

    # Change ownership of the mount point to current user
    # This allows the user to read/write files
    sudo chown $USER:$USER "$MOUNT_POINT"

    # If there are already files, change their ownership too
    if [ "$(ls -A $MOUNT_POINT 2>/dev/null)" ]; then
        sudo chown -R $USER:$USER "$MOUNT_POINT"/*
    fi

    echo "✓ Permissions set for user access"

    echo ""
    echo "======================================================================"
    echo "                           SUCCESS!"
    echo "======================================================================"
    echo ""
    echo "Your secure storage is now accessible at:"
    echo "    $MOUNT_POINT"
    echo ""
    echo "Easy access:"
    echo "  • Open file manager and go to Home folder"
    echo "  • Look for 'SecureStorage' folder"
    echo "  • Or in terminal: cd ~/SecureStorage"
    echo ""
    echo "You can now:"
    echo "  • Drag and drop files"
    echo "  • Edit documents"
    echo "  • Create new folders"
    echo ""
    echo "IMPORTANT: When finished, run:"
    echo "    sudo ./lock_storage.sh"
    echo ""
    echo "======================================================================"
else
    echo ""
    echo "======================================================================"
    echo "                       MOUNT FAILED"
    echo "======================================================================"
    echo ""
    echo "Possible reasons:"
    echo "  • Wrong password"
    echo "  • Wrong partition selected"
    echo "  • Volume already mounted"
    echo "  • veracrypt not installed"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check if already mounted: mount | grep secure_storage"
    echo "  2. Try unmounting first: sudo veracrypt -d"
    echo "  3. Verify veracrypt: which veracrypt"
    echo ""
    rmdir "$MOUNT_POINT" 2>/dev/null
    exit 1
fi
