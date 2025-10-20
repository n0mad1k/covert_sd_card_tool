#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os
import shutil
from datetime import datetime
import time
import json

# Global variables
DEBUG = False
FAST_MODE = False
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_FILE = f"covert_sd_setup_{TIMESTAMP}.log"
CREATE_KALI = False
CREATE_DOCS = False
CREATE_TAILS = False
CREATE_CUSTOM = False
KALI_ISO = ""
TAILS_ISO = ""
CUSTOM_ISO = ""
DRIVE = ""

def log(message):
    """Logs a message to both the log file and the terminal."""
    with open(LOG_FILE, "a") as log_file:
        log_file.write(message + "\n")
    print(message)

def run_command(command, shell=False, interactive=False):
    """
    Runs a system command.
    
    Args:
        command (list or str): The command to execute.
        shell (bool): Whether to execute the command through the shell.
        interactive (bool): If True, streams the command's output live.
    """
    if DEBUG:
        log(f"Running command: {command}")
    try:
        if interactive:
            # Use subprocess.run with no stdout/stderr capture for truly interactive commands
            # This allows the command to directly interact with the terminal
            result = subprocess.run(command, shell=shell, check=True)
            return
        else:
            # Handle non-interactive commands
            if isinstance(command, list):
                result = subprocess.run(
                    command,
                    shell=shell,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
            else:
                result = subprocess.run(
                    command,
                    shell=shell,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
            if result.stdout:
                log(result.stdout.strip())
            if result.stderr:
                log(result.stderr.strip())
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {e}\nOutput: {e.stdout}\nError: {e.stderr}")
        sys.exit(1)

def check_dependencies():
    """Checks and installs missing dependencies."""
    dependencies = [
        "parted", "cryptsetup", "lsblk", "dd", "sgdisk", "wipefs",
        "bc", "fdisk", "veracrypt", "lsof", "fuser", "mountpoint", "udevadm"
    ]
    missing = []
    for dep in dependencies:
        if not shutil.which(dep):
            missing.append(dep)
    if missing:
        log(f"Missing dependencies: {', '.join(missing)}")
        install = input(f"Do you want to install the missing dependencies? (y/n) [Default: y]: ") or "y"
        if install.lower() == "y":
            run_command(["sudo", "apt", "update"])
            run_command(["sudo", "apt", "install", "-y"] + missing)
        else:
            log("Cannot proceed without installing dependencies. Exiting.")
            sys.exit(1)

def list_drives():
    """Lists all available drives."""
    log("Available drives:")
    result = subprocess.run(["lsblk", "-J", "-o", "NAME,SIZE,TYPE"], capture_output=True, text=True)
    try:
        lsblk_output = json.loads(result.stdout)
        for device in lsblk_output['blockdevices']:
            if device['type'] == 'disk':
                name = device['name']
                size = device['size']
                drive = f"/dev/{name} {size}"
                log(drive)
    except json.JSONDecodeError:
        log("Error: Unable to parse lsblk output.")
        sys.exit(1)

def get_partition_name(drive, partition_number):
    """
    Generates the partition name based on the drive and partition number.
    
    Args:
        drive (str): The drive path (e.g., /dev/sda).
        partition_number (int): The partition number.
        
    Returns:
        str: The full partition path (e.g., /dev/sda1 or /dev/nvme0n1p1).
    """
    if 'nvme' in drive or 'mmcblk' in drive:
        return f"{drive}p{partition_number}"
    else:
        return f"{drive}{partition_number}"

def prepare_drive(drive):
    """
    Unmounts any mounted partitions, disables swap, and kills processes using the drive.
    
    Args:
        drive (str): The drive to prepare (e.g., /dev/sda).
    """
    # Unmount all mounted partitions
    result = subprocess.run(["lsblk", "-lnp", drive], capture_output=True, text=True)
    for line in result.stdout.strip().splitlines():
        parts = line.strip().split()
        if len(parts) >= 7 and parts[6]:  # If mountpoint is not empty
            part = parts[0]
            log(f"Unmounting {part}...")
            run_command(["sudo", "umount", "-l", part])

    # Disable swap if it's on the drive
    with open("/proc/swaps") as swaps_file:
        for line in swaps_file:
            if drive in line:
                swap_part = line.strip().split()[0]
                log(f"Disabling swap on {swap_part}...")
                run_command(["sudo", "swapoff", swap_part])

    # Kill any processes using the drive
    log(f"Checking for processes using {drive}...")
    result = subprocess.run(["sudo", "lsof", drive], capture_output=True, text=True)
    if result.stdout.strip():
        log(f"Processes using {drive}:\n{result.stdout}")
        kill = input(f"Do you want to kill these processes? (y/n) [Default: y]: ") or "y"
        if kill.lower() == "y":
            run_command(["sudo", "fuser", "-k", drive])
            log(f"Killed processes using {drive}.")
        else:
            log("Cannot proceed while processes are using the drive. Exiting.")
            sys.exit(1)
    else:
        log(f"No processes are using {drive}.")

def setup_usb():
    """
    Sets up the bootable USB (Tails or Kali) and creates additional partitions if required.
    """
    global DRIVE
    log("Setting up bootable USB or preparing partitions...")
    list_drives()
    DRIVE = input("Enter the drive to use for USB (e.g., /dev/sda) [Default: /dev/sda]: ") or "/dev/sda"

    confirm = input(f"You have selected {DRIVE}. Is this correct? (y/n) [Default: y]: ") or "y"
    if confirm.lower() != "y":
        log("Drive selection canceled. Exiting.")
        sys.exit(1)

    prepare_drive(DRIVE)

    if CREATE_KALI or CREATE_TAILS or CREATE_DOCS:
        wipe = input(f"Do you want to wipe the drive {DRIVE} before starting? (y/n) [Default: n]: ") or "n"
        if wipe.lower() == "y":
            log(f"Wiping {DRIVE} and clearing any existing file system or encryption signatures...")
            log("This will securely overwrite the entire drive with random data. This may take a while...")
            confirm_wipe = input(f"Are you ABSOLUTELY sure you want to completely wipe {DRIVE}? Type 'WIPE' to confirm: ")
            if confirm_wipe == "WIPE":
                run_command(["sudo", "wipefs", "--all", DRIVE])
                run_command(["sudo", "sgdisk", "--zap-all", DRIVE])
                # Secure wipe using shred - 3 passes with random data, then zeros
                run_command(["sudo", "shred", "-vfz", "-n", "3", DRIVE], interactive=True)
                log(f"{DRIVE} securely wiped successfully.")
            else:
                log("Wipe canceled. Proceeding without full wipe (only clearing partition table)...")
                run_command(["sudo", "wipefs", "--all", DRIVE])
                run_command(["sudo", "sgdisk", "--zap-all", DRIVE])

    # Initialize variables to track if ISO has been written
    iso_written = False

    if CREATE_KALI or CREATE_TAILS or CREATE_CUSTOM:
        global KALI_ISO, TAILS_ISO, CUSTOM_ISO
        if CREATE_KALI:
            if not KALI_ISO:
                KALI_ISO = input("Enter the path to the Kali ISO file: ")
            if not os.path.isfile(KALI_ISO):
                log(f"Error: Kali ISO file not found at {KALI_ISO}")
                sys.exit(1)
            ISO_PATH = KALI_ISO
        elif CREATE_TAILS:
            if not TAILS_ISO:
                TAILS_ISO = input("Enter the path to the Tails ISO file: ")
            if not os.path.isfile(TAILS_ISO):
                log(f"Error: Tails ISO file not found at {TAILS_ISO}")
                sys.exit(1)
            ISO_PATH = TAILS_ISO
        elif CREATE_CUSTOM:
            if not CUSTOM_ISO:
                CUSTOM_ISO = input("Enter the path to your custom ISO file: ")
            if not os.path.isfile(CUSTOM_ISO):
                log(f"Error: Custom ISO file not found at {CUSTOM_ISO}")
                sys.exit(1)
            ISO_PATH = CUSTOM_ISO

        if CREATE_TAILS:
            # For Tails, flash the ISO to the entire drive without any partitioning
            log(f"Flashing Tails ISO to {DRIVE}...")
            run_command(f"sudo dd if='{ISO_PATH}' of='{DRIVE}' bs=64M status=progress conv=fdatasync", shell=True, interactive=True)
            log(f"Tails ISO flashed to {DRIVE} successfully.")
            iso_written = True
        else:
            # For Kali or Custom ISO, flash and proceed with partition setup
            log(f"Flashing ISO to {DRIVE}...")
            run_command(f"sudo dd if='{ISO_PATH}' of='{DRIVE}' bs=64M status=progress conv=fdatasync", shell=True, interactive=True)
            log(f"ISO flashed to {DRIVE} successfully.")
            iso_written = True

    # After writing ISO, set up partitions accordingly
    if iso_written:
        if CREATE_KALI or CREATE_CUSTOM:
            # Both Kali and custom ISOs use the same partitioning approach
            fix_partition_table()
        elif CREATE_TAILS:
            if CREATE_DOCS:
                # For Tails with docs, add partitions after Tails
                fix_partition_table_tails()
            else:
                # Tails only, no additional partitions
                log("Tails installation complete. No additional partitions requested.")
    elif CREATE_DOCS:
        # If no ISO was written, just set up documents partition
        fix_partition_table_docs_only()

def fix_partition_table_docs_only():
    """
    Sets up partitions solely for encrypted documents without altering existing OS partitions.
    """
    log("Setting up partitions for documents only...")

    # Clear existing GPT label to start fresh
    run_command(f"sudo parted -a optimal -s {DRIVE} mklabel gpt", shell=True)
    run_command(f"sudo partprobe {DRIVE}", shell=True)
    run_command("sudo udevadm settle", shell=True)
    time.sleep(5)  # Increased sleep to ensure partitions are recognized

    # Get the total size of the drive in bytes
    result = subprocess.run(["lsblk", "-b", "-d", "-n", "-o", "SIZE", DRIVE], capture_output=True, text=True)
    try:
        total_size_bytes = int(result.stdout.strip())
    except ValueError:
        log(f"Error: Unable to determine drive size. lsblk output: {result.stdout}")
        sys.exit(1)
    total_size_mib = total_size_bytes / (1024 * 1024)  # Convert to MiB
    total_size_gb = total_size_mib / 1024  # Convert to GiB
    available_gb = (total_size_mib - 1024) / 1024  # Minus 1GB reserved for scripts

    log(f"Total drive size: {total_size_gb:.2f} GB ({total_size_mib:.0f} MiB)")
    log(f"Available space for documents (minus 1GB for scripts): {available_gb:.2f} GB")

    # Ask for document partition size
    size_docs = input("Enter size for documents partition in GB (leave blank to use remaining space minus 1GB): ")
    start_docs_mib = 1  # Starting immediately after the first MiB
    if size_docs:
        try:
            size_docs_gb = float(size_docs)
            end_docs_mib = start_docs_mib + (size_docs_gb * 1024)
            if end_docs_mib > (total_size_mib - 1024):
                log("Error: Documents partition size exceeds available space when reserving 1GB for unencrypted partition.")
                sys.exit(1)
        except ValueError:
            log("Invalid size entered for documents partition. Exiting.")
            sys.exit(1)
    else:
        end_docs_mib = total_size_mib - 1024  # Reserve 1GB for unencrypted partition

    # Create documents partition
    run_command(f"sudo parted -a optimal -s {DRIVE} mkpart primary {start_docs_mib}MiB {end_docs_mib}MiB", shell=True)
    log("Created documents partition.")

    # Create unencrypted partition
    start_unencrypted_mib = end_docs_mib
    run_command(f"sudo parted -a optimal -s {DRIVE} mkpart primary {start_unencrypted_mib}MiB 100%", shell=True)
    log("Created unencrypted partition for scripts/instructions.")

    # Refresh partition table to recognize new partitions
    run_command(f"sudo partprobe {DRIVE}", shell=True)
    run_command("sudo udevadm settle", shell=True)
    time.sleep(5)  # Increased sleep to ensure partitions are recognized

    setup_unencrypted_partition()
    setup_docs_partition()

def fix_partition_table_tails():
    """
    Adds encrypted documents partition after Tails installation without breaking boot.
    Tails creates its own partition table, so we extend it carefully.
    """
    log("Adding encrypted documents partition after Tails installation...")

    # Wait for Tails partitions to settle
    run_command(f"sudo partprobe {DRIVE}", shell=True)
    run_command("sudo udevadm settle", shell=True)
    time.sleep(5)

    # Get current partition information
    result = subprocess.run(["sudo", "parted", "-s", DRIVE, "unit", "MiB", "print"], capture_output=True, text=True)
    log("Current partition table after Tails installation:")
    log(result.stdout)

    # Find the end of the last Tails partition
    last_partition_end = None
    partition_lines = [line for line in result.stdout.strip().splitlines() if line.strip() and line.strip()[0].isdigit()]

    if partition_lines:
        # Get the last partition's end position
        last_line = partition_lines[-1]
        parts = last_line.strip().split()
        if len(parts) >= 3:
            last_partition_end = parts[2].replace('MiB', '')

    if last_partition_end is None:
        log("Error: Could not determine end of Tails partitions.")
        sys.exit(1)

    log(f"Last Tails partition ends at: {last_partition_end}MiB")

    # Get the total size of the drive
    result = subprocess.run(["lsblk", "-b", "-d", "-n", "-o", "SIZE", DRIVE], capture_output=True, text=True)
    try:
        total_size_bytes = int(result.stdout.strip())
    except ValueError:
        log(f"Error: Unable to determine drive size. lsblk output: {result.stdout}")
        sys.exit(1)
    total_size_mib = total_size_bytes / (1024 * 1024)
    total_size_gb = total_size_mib / 1024
    available_after_tails_mib = total_size_mib - float(last_partition_end)
    available_after_tails_gb = available_after_tails_mib / 1024

    log(f"Total drive size: {total_size_gb:.2f} GB ({total_size_mib:.0f} MiB)")
    log(f"Available space after Tails: {available_after_tails_gb:.2f} GB")

    if available_after_tails_gb < 2:
        log(f"Warning: Only {available_after_tails_gb:.2f} GB available after Tails. Need at least 2GB for docs + tools partitions.")
        proceed = input("Continue anyway? (y/n) [Default: n]: ") or "n"
        if proceed.lower() != "y":
            log("Partition setup canceled.")
            return

    # Set up documents partition
    start_docs_mib = float(last_partition_end)
    remaining_after_tails_gb = (total_size_mib - start_docs_mib) / 1024
    log(f"Remaining space for documents: {remaining_after_tails_gb:.2f} GB (will reserve 1GB for tools partition)")

    size_docs = input("Enter size for documents partition in GB (leave blank to use remaining space minus 1GB): ")
    if size_docs:
        try:
            size_docs_gb = float(size_docs)
            end_docs_mib = start_docs_mib + (size_docs_gb * 1024)
            if end_docs_mib > (total_size_mib - 1024):
                log("Error: Documents partition size exceeds available space when reserving 1GB for tools partition.")
                sys.exit(1)
        except ValueError:
            log("Invalid size entered for documents partition. Exiting.")
            sys.exit(1)
    else:
        end_docs_mib = total_size_mib - 1024  # Reserve 1GB for tools partition

    run_command(f"sudo parted -a optimal -s {DRIVE} mkpart primary {start_docs_mib}MiB {end_docs_mib}MiB", shell=True)
    log("Created documents partition after Tails.")

    # Create unencrypted tools partition
    start_unencrypted_mib = end_docs_mib
    run_command(f"sudo parted -a optimal -s {DRIVE} mkpart primary {start_unencrypted_mib}MiB 100%", shell=True)
    log("Created tools partition for scripts/instructions.")

    # Refresh partition table
    run_command(f"sudo partprobe {DRIVE}", shell=True)
    run_command("sudo udevadm settle", shell=True)
    time.sleep(5)

    setup_docs_partition()
    setup_unencrypted_partition()

    log("Tails + encrypted documents partition setup complete!")

def fix_partition_table():
    """
    Fixes the partition table for Kali Linux by adding persistence and documents partitions.
    """
    log("Fixing partition table to reclaim remaining space...")

    # Attempt to delete partition 2 if it exists
    try:
        run_command(f"sudo parted -a optimal -s {DRIVE} rm 2", shell=True)
        log("Deleted partition 2.")
    except SystemExit:
        log("No partition 2 to delete.")

    # Get the end of partition 1
    result = subprocess.run(["sudo", "parted", "-s", DRIVE, "unit", "MiB", "print"], capture_output=True, text=True)
    end_of_p1 = None
    for line in result.stdout.strip().splitlines():
        if line.strip().startswith("1"):
            parts = line.strip().split()
            if len(parts) >= 3:
                end_of_p1 = parts[2].replace('MiB', '')
                break
    if end_of_p1 is None:
        log("Error: Could not find end of partition 1.")
        sys.exit(1)

    log(f"End of partition 1: {end_of_p1}MiB")

    # Get the total size of the drive in bytes
    result = subprocess.run(["lsblk", "-b", "-d", "-n", "-o", "SIZE", DRIVE], capture_output=True, text=True)
    try:
        total_size_bytes = int(result.stdout.strip())
    except ValueError:
        log(f"Error: Unable to determine drive size. lsblk output: {result.stdout}")
        sys.exit(1)
    total_size_mib = total_size_bytes / (1024 * 1024)  # Convert to MiB
    total_size_gb = total_size_mib / 1024  # Convert to GiB
    available_after_p1_gb = (total_size_mib - float(end_of_p1)) / 1024

    log(f"Total drive size: {total_size_gb:.2f} GB ({total_size_mib:.0f} MiB)")
    log(f"Available space after partition 1: {available_after_p1_gb:.2f} GB")

    # Ask for persistence partition size
    size_persistence = input("Enter size for persistence partition in GB (e.g., 4): ") or "4"
    try:
        size_persistence_gb = float(size_persistence)
    except ValueError:
        log("Invalid size entered for persistence partition. Exiting.")
        sys.exit(1)

    start_persistence_mib = float(end_of_p1)
    end_persistence_mib = start_persistence_mib + (size_persistence_gb * 1024)

    if end_persistence_mib > total_size_mib:
        log("Error: Persistence partition size exceeds available space.")
        sys.exit(1)

    # Create persistence partition
    run_command(f"sudo parted -a optimal -s {DRIVE} mkpart primary ext4 {start_persistence_mib}MiB {end_persistence_mib}MiB", shell=True)
    log("Created persistence partition.")

    # Set up documents partition
    start_docs_mib = end_persistence_mib
    remaining_after_persistence_gb = (total_size_mib - end_persistence_mib) / 1024
    log(f"Remaining space after persistence partition: {remaining_after_persistence_gb:.2f} GB (will reserve 1GB for scripts)")

    size_docs = input("Enter size for documents partition in GB (leave blank to use remaining space minus 1GB): ")
    if size_docs:
        try:
            size_docs_gb = float(size_docs)
            end_docs_mib = start_docs_mib + (size_docs_gb * 1024)
            if end_docs_mib > (total_size_mib - 1024):
                log("Error: Documents partition size exceeds available space when reserving 1GB for unencrypted partition.")
                sys.exit(1)
        except ValueError:
            log("Invalid size entered for documents partition. Exiting.")
            sys.exit(1)
    else:
        end_docs_mib = total_size_mib - 1024  # Reserve 1GB for unencrypted partition

    run_command(f"sudo parted -a optimal -s {DRIVE} mkpart primary {start_docs_mib}MiB {end_docs_mib}MiB", shell=True)
    log("Created documents partition.")

    # Create unencrypted partition
    start_unencrypted_mib = end_docs_mib
    run_command(f"sudo parted -a optimal -s {DRIVE} mkpart primary {start_unencrypted_mib}MiB 100%", shell=True)
    log("Created unencrypted partition for scripts/instructions.")

    # Refresh partition table to recognize new partitions
    run_command(f"sudo partprobe {DRIVE}", shell=True)
    run_command("sudo udevadm settle", shell=True)
    time.sleep(5)  # Increased sleep to ensure partitions are recognized

    setup_kali_partition()
    if CREATE_DOCS:
        setup_docs_partition()
    setup_unencrypted_partition()

def setup_kali_partition():
    """
    Configures the persistence partition for Kali Linux.
    """
    global DRIVE
    PERSIST_PART = get_partition_name(DRIVE, 2)

    # Check if partition exists
    if not os.path.exists(PERSIST_PART):
        log(f"Error: Partition {PERSIST_PART} does not exist.")
        sys.exit(1)

    run_command(["sudo", "wipefs", "--all", PERSIST_PART])

    log("Configuring encrypted persistence partition...")

    log("You will be prompted to enter a passphrase for the persistence partition.")
    log("Please choose a strong passphrase and remember it!")
    log("When asked 'Are you sure? (Type YES in capital letters):', type: YES")
    log("Then enter your passphrase twice when prompted.")

    if FAST_MODE:
        luks_format_cmd = (
            f"sudo cryptsetup luksFormat '{PERSIST_PART}' "
            f"--type luks1 "
            f"--cipher aes-cbc-essiv:sha256 "
            f"--key-size 256 "
            f"--hash sha256 "
            f"--iter-time 1000 "
            f"--verify-passphrase"
        )
        mkfs_cmd = f"sudo mkfs.ext3 -L persistence /dev/mapper/kali_USB"
    else:
        luks_format_cmd = (
            f"sudo cryptsetup luksFormat '{PERSIST_PART}' "
            f"--cipher aes-xts-plain64 "
            f"--key-size 512 "
            f"--hash sha512 "
            f"--iter-time 5000 "
            f"--verify-passphrase"
        )
        mkfs_cmd = f"sudo mkfs.ext4 -L persistence /dev/mapper/kali_USB"

    run_command(luks_format_cmd, shell=True, interactive=True)
    time.sleep(2)
    run_command(f"sudo cryptsetup luksOpen '{PERSIST_PART}' kali_USB", shell=True, interactive=True)
    run_command(mkfs_cmd, shell=True)

    run_command("sudo mkdir -p /mnt/kali_USB", shell=True)
    run_command("sudo mount /dev/mapper/kali_USB /mnt/kali_USB", shell=True)
    run_command('echo "/ union" | sudo tee /mnt/kali_USB/persistence.conf', shell=True)
    run_command("sudo umount /mnt/kali_USB", shell=True)
    run_command("sudo cryptsetup luksClose kali_USB", shell=True)

    log("Kali persistence setup complete.")

def setup_docs_partition():
    """
    Configures the VeraCrypt encrypted documents partition.
    """
    global DRIVE
    DOCS_PART = get_partition_name(DRIVE, get_last_partition_number() - 1)

    # Check if the partition exists
    if not os.path.exists(DOCS_PART):
        log(f"Error: Partition {DOCS_PART} does not exist.")
        sys.exit(1)

    # Force wipe existing filesystem signatures
    run_command(["sudo", "wipefs", "--all", "--force", DOCS_PART])
    log(f"Removed existing filesystem signatures from {DOCS_PART}.")

    log("\n" + "="*70)
    log("ENCRYPTED VOLUME SETUP")
    log("="*70)
    log("\nYou will now create an encrypted volume for sensitive documents.")
    log("\nWhat you'll be asked:")
    log("  1. PASSWORD: Enter a strong passphrase (you'll type it twice)")
    log("     - Use at least 20 characters")
    log("     - Mix uppercase, lowercase, numbers, and symbols")
    log("     - Avoid dictionary words or personal information")
    log("  2. PIM (Personal Iterations Multiplier):")
    log("     - RECOMMENDED: Enter 2000 for maximum security")
    log("     - Minimum acceptable: 1000")
    log("     - Higher = more secure but slower unlock (2-3 seconds)")
    log("  3. KEYFILES: Leave blank unless you know what you're doing")
    log("\nIMPORTANT: Remember your password! There is NO password recovery!")
    log("="*70)
    input("\nPress ENTER to continue with encryption setup...")

    log("\nConfiguring VeraCrypt encryption for documents partition...")

    # Always use maximum security for documents partition (ignore FAST_MODE)
    # Triple cascade encryption with strongest hash
    veracrypt_create_cmd = (
        f"veracrypt --text --create '{DOCS_PART}' "
        f"--encryption AES-Twofish-Serpent "
        f"--hash SHA-512 "
        f"--filesystem ext4 "
        f"--volume-type normal "
        f"--pim 2000 "  # Enforce strong PIM for maximum security
    )

    run_command(veracrypt_create_cmd, shell=True, interactive=True)
    log("Encrypted documents partition setup complete.")

def setup_unencrypted_partition():
    """
    Sets up the unencrypted partition for scripts and instructions.
    """
    global DRIVE
    UNENCRYPTED_PART = get_partition_name(DRIVE, get_last_partition_number())

    # Check if the partition exists
    if not os.path.exists(UNENCRYPTED_PART):
        log(f"Error: Partition {UNENCRYPTED_PART} does not exist.")
        sys.exit(1)

    log(f"Attempting to format partition {UNENCRYPTED_PART} with FAT32 filesystem.")
    run_command(f"sudo mkfs.vfat -n 'TOOLS' {UNENCRYPTED_PART}", shell=True)
    log("Formatted unencrypted partition with FAT32 filesystem.")

    run_command("sudo mkdir -p /mnt/unencrypted", shell=True)
    run_command(f"sudo mount {UNENCRYPTED_PART} /mnt/unencrypted", shell=True)

    instructions = f"""
INSTRUCTIONS FOR ACCESSING SECURE STORAGE

To access your secure partition:
  1. Run: sudo ./mount_storage.sh
  2. Enter your password when prompted
  3. Your files will be available at /mnt/secure_storage

To safely lock your storage:
  1. Close all files and applications using the storage
  2. Run: sudo ./lock_storage.sh
  3. Your data is now secured

IMPORTANT: Always lock your storage before removing the device.
"""

    with open("/tmp/README.txt", "w") as readme_file:
        readme_file.write(instructions)
    run_command("sudo cp /tmp/README.txt /mnt/unencrypted/README.txt", shell=True)
    run_command("sudo rm /tmp/README.txt", shell=True)
    log("Created README.txt with mounting instructions.")

    mount_script = """#!/bin/bash
# Script to mount secure storage partition

echo "=== Secure Storage Mount ==="
echo ""
echo "Available storage devices:"
lsblk -o NAME,SIZE,TYPE,LABEL | grep -E 'disk|part'
echo ""
read -p "Enter the partition path (e.g., /dev/sdb3): " DRIVE_PATH

if [ -z "$DRIVE_PATH" ]; then
    echo "Error: No partition specified."
    exit 1
fi

if [ ! -b "$DRIVE_PATH" ]; then
    echo "Error: $DRIVE_PATH is not a valid block device."
    exit 1
fi

echo ""
echo "Mounting secure storage from $DRIVE_PATH..."
sudo mkdir -p /mnt/secure_storage

# Mount the encrypted volume
if sudo veracrypt --text --mount "$DRIVE_PATH" /mnt/secure_storage; then
    echo ""
    echo "SUCCESS: Secure storage is now accessible at /mnt/secure_storage"
    echo ""
    echo "Remember to run ./lock_storage.sh when finished!"
else
    echo ""
    echo "ERROR: Failed to mount storage. Check your password and try again."
    sudo rmdir /mnt/secure_storage 2>/dev/null
    exit 1
fi
"""

    with open("/tmp/mount_storage.sh", "w") as script_file:
        script_file.write(mount_script)
    run_command("sudo cp /tmp/mount_storage.sh /mnt/unencrypted/mount_storage.sh", shell=True)
    run_command("sudo chmod +x /mnt/unencrypted/mount_storage.sh", shell=True)
    run_command("sudo rm /tmp/mount_storage.sh", shell=True)
    log("Created mount_storage.sh script.")

    cleanup_script = """#!/bin/bash
# Script to safely lock secure storage

echo "=== Secure Storage Lock ==="
echo ""

# Check if storage is mounted
if mountpoint -q /mnt/secure_storage; then
    echo "Checking for open files..."

    # Check if any processes are using the mount
    if sudo lsof /mnt/secure_storage 2>/dev/null | grep -q /mnt/secure_storage; then
        echo ""
        echo "WARNING: Files are still open in the secure storage!"
        echo "Open files/processes:"
        sudo lsof /mnt/secure_storage 2>/dev/null
        echo ""
        read -p "Force close and lock anyway? (y/N): " FORCE
        if [ "$FORCE" != "y" ] && [ "$FORCE" != "Y" ]; then
            echo "Lock cancelled. Please close all files and try again."
            exit 1
        fi
    fi

    echo ""
    echo "Locking secure storage..."

    # Sync any pending writes
    sync

    # Dismount the encrypted volume
    if sudo veracrypt --text --dismount /mnt/secure_storage; then
        sudo rmdir /mnt/secure_storage 2>/dev/null
        echo ""
        echo "SUCCESS: Secure storage is now locked."
        echo "Your data is safe."
    else
        echo ""
        echo "ERROR: Failed to lock storage. Try closing all applications and run again."
        exit 1
    fi
else
    echo "Secure storage is not currently mounted."
    echo "Nothing to lock."
fi
"""

    with open("/tmp/lock_storage.sh", "w") as script_file:
        script_file.write(cleanup_script)
    run_command("sudo cp /tmp/lock_storage.sh /mnt/unencrypted/lock_storage.sh", shell=True)
    run_command("sudo chmod +x /mnt/unencrypted/lock_storage.sh", shell=True)
    run_command("sudo rm /tmp/lock_storage.sh", shell=True)
    log("Created lock_storage.sh script.")

    run_command("sudo umount /mnt/unencrypted", shell=True)
    log("Unencrypted partition setup complete.")

def get_last_partition_number():
    """
    Returns the highest partition number on the DRIVE.
    
    Returns:
        int: The highest partition number.
    """
    result = subprocess.run(["lsblk", "-ln", "-o", "NAME", DRIVE], capture_output=True, text=True)
    partitions = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    partition_numbers = []
    for part in partitions:
        if 'p' in part:
            # Handle /dev/nvme0n1p1 format
            if part.startswith(os.path.basename(DRIVE)):
                num = part.replace(os.path.basename(DRIVE), '').replace('p', '')
                if num.isdigit():
                    partition_numbers.append(int(num))
        else:
            # Handle /dev/sda1 format
            if part.startswith(os.path.basename(DRIVE)):
                num = part.replace(os.path.basename(DRIVE), '')
                if num.isdigit():
                    partition_numbers.append(int(num))
    if not partition_numbers:
        log(f"No partitions found on {DRIVE}.")
        sys.exit(1)
    return max(partition_numbers)

def main():
    """
    The main function that parses arguments and orchestrates the setup process.
    """
    global DEBUG, FAST_MODE, CREATE_KALI, CREATE_DOCS, CREATE_TAILS, KALI_ISO, TAILS_ISO, DRIVE, CREATE_CUSTOM, CUSTOM_ISO

    CREATE_CUSTOM = False
    CUSTOM_ISO = ""

    parser = argparse.ArgumentParser(description="Covert SD Card Tool")
    
    # Creating a mutually exclusive group for -a and -t to prevent their simultaneous use
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", "--all", action="store_true", help="Set up both OS bootable USB and documents partition")
    group.add_argument("-t", "--tails", action="store_true", help="Create Tails bootable USB (no persistence)")
    
    # Other arguments remain outside the mutually exclusive group
    parser.add_argument("-k", "--kali", action="store_true", help="Create Kali bootable USB and persistence partition")
    parser.add_argument("-d", "--docs", action="store_true", help="Create encrypted documents partition")
    parser.add_argument("-c", "--custom", action="store_true", help="Create custom ISO bootable USB (like Kali, with persistence)")
    parser.add_argument("-i", "--iso", help="Path to the ISO file (Kali, Tails, or custom)")
    parser.add_argument("--fast", action="store_true", help="Enable fast setup with less secure encryption")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Prevent using -a with -t; argparse handles this due to mutually exclusive group
    # However, if you want to provide a custom error message or additional handling, you can add it here

    if not any([args.all, args.kali, args.docs, args.tails, args.custom]):
        parser.print_help()
        sys.exit(1)

    DEBUG = args.debug
    if DEBUG:
        log("Debug mode enabled")

    FAST_MODE = args.fast
    if FAST_MODE:
        log("Fast mode enabled: Using less secure encryption for quicker setup.")

    if args.all:
        CREATE_DOCS = True
        # When -a is used without -t, default to creating Kali
        CREATE_KALI = True
    else:
        CREATE_KALI = args.kali
        CREATE_DOCS = args.docs
        CREATE_TAILS = args.tails
        CREATE_CUSTOM = args.custom

    if args.iso:
        if CREATE_KALI:
            KALI_ISO = args.iso
        elif CREATE_TAILS:
            TAILS_ISO = args.iso
        elif CREATE_CUSTOM:
            CUSTOM_ISO = args.iso

    check_dependencies()
    setup_usb()
    log("Partition setup complete.")

if __name__ == "__main__":
    main()
