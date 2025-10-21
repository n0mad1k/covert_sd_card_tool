#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os
import shutil
from datetime import datetime
import time
import json
import urllib.request
import tempfile

# Global variables
DEBUG = False
FAST_MODE = False
PARANOID_MODE = False
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

def run_command(command, shell=False, interactive=False, ignore_enospc=False):
    """
    Runs a system command.

    Args:
        command (list or str): The command to execute.
        shell (bool): Whether to execute the command through the shell.
        interactive (bool): If True, streams the command's output live.
        ignore_enospc (bool): If True, don't exit on "No space left" error (for dd filling disk).
    """
    if DEBUG:
        log(f"Running command: {command}")
    try:
        if interactive:
            # Use subprocess.run with no stdout/stderr capture for truly interactive commands
            # This allows the command to directly interact with the terminal
            # Don't use check=True if we want to ignore ENOSPC
            result = subprocess.run(command, shell=shell, check=not ignore_enospc)
            if ignore_enospc and result.returncode != 0:
                # For dd, exit code 1 with ENOSPC is success (filled the disk)
                return
            elif result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, command)
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

def download_file(url, destination, description="file"):
    """
    Downloads a file with progress indication.

    Args:
        url (str): URL to download from
        destination (str): Local path to save file
        description (str): Description for user feedback
    """
    try:
        log(f"Downloading {description}...")
        log(f"  From: {url}")
        log(f"  To: {destination}")

        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, (downloaded * 100) // total_size)
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                # Use \r to overwrite the same line
                print(f"\r  Progress: {percent}% ({mb_downloaded:.1f} MB / {mb_total:.1f} MB)", end='', flush=True)

        urllib.request.urlretrieve(url, destination, reporthook=progress_hook)
        print()  # New line after progress
        log(f"✓ {description} downloaded successfully")
        return True
    except Exception as e:
        log(f"✗ Failed to download {description}: {e}")
        return False

def download_portable_veracrypt():
    """
    Downloads portable VeraCrypt binaries for Windows, Linux, and macOS.
    Returns the path to a temporary directory containing the downloads.
    """
    log("\n" + "="*70)
    log("DOWNLOADING PORTABLE VERACRYPT")
    log("="*70)
    log("\nTo make this device work on ANY computer without software installation,")
    log("we need to download portable VeraCrypt for Windows, Linux, and macOS.")
    log("")
    log("Total download size: ~86-90 MB")
    log("  • Windows Portable: ~39 MB")
    log("  • Linux AppImage: ~13 MB")
    log("  • Linux .deb Installer: ~13 MB")
    log("  • macOS DMG: ~22 MB")
    log("")
    log("This is a one-time download that will be stored on your device.")
    log("")

    # Create temp directory for downloads
    temp_dir = tempfile.mkdtemp(prefix="veracrypt_download_")
    log(f"Using temporary directory: {temp_dir}")
    log("")

    # Get latest VeraCrypt version from GitHub
    log("Fetching latest VeraCrypt version from GitHub...")
    try:
        import urllib.request
        import json
        with urllib.request.urlopen("https://api.github.com/repos/veracrypt/VeraCrypt/releases/latest") as response:
            release_data = json.loads(response.read().decode())
            VC_TAG = release_data["tag_name"]  # e.g., "VeraCrypt_1.26.24"
            VC_VERSION = VC_TAG.replace("VeraCrypt_", "")  # e.g., "1.26.24"
            log(f"✓ Latest version: {VC_VERSION}")
    except Exception as e:
        log(f"⚠ Warning: Could not fetch latest version ({e})")
        log("  Falling back to version 1.26.24")
        VC_TAG = "VeraCrypt_1.26.24"
        VC_VERSION = "1.26.24"

    log("")

    downloads = {
        "Windows Portable": {
            "url": f"https://github.com/veracrypt/VeraCrypt/releases/download/{VC_TAG}/VeraCrypt.Portable.{VC_VERSION}.exe",
            "filename": "VeraCrypt-Portable-Windows.exe",
            "required": True
        },
        "Linux Portable AppImage": {
            "url": f"https://github.com/veracrypt/VeraCrypt/releases/download/{VC_TAG}/VeraCrypt-{VC_VERSION}-x86_64.AppImage",
            "filename": "VeraCrypt-Portable-Linux.AppImage",
            "required": True
        },
        "Linux DEB Installer": {
            "url": f"https://github.com/veracrypt/VeraCrypt/releases/download/{VC_TAG}/veracrypt-{VC_VERSION}-Ubuntu-22.04-amd64.deb",
            "filename": "veracrypt-Ubuntu-22.04-amd64.deb",
            "required": False
        },
        "macOS": {
            "url": f"https://github.com/veracrypt/VeraCrypt/releases/download/{VC_TAG}/VeraCrypt_{VC_VERSION}.dmg",
            "filename": "VeraCrypt-MacOS.dmg",
            "required": False
        }
    }

    success_count = 0
    required_count = 0

    for platform, info in downloads.items():
        log(f"\n[{platform}]")
        dest_path = os.path.join(temp_dir, info["filename"])

        if info.get("required"):
            required_count += 1

        if download_file(info["url"], dest_path, f"{platform} VeraCrypt"):
            success_count += 1

            # Make Linux AppImage executable
            if "AppImage" in info["filename"]:
                try:
                    os.chmod(dest_path, 0o755)
                    log(f"  ✓ Made executable")
                except Exception as e:
                    log(f"  ⚠ Warning: Could not make executable: {e}")
        else:
            if info.get("required"):
                log(f"  ✗ ERROR: {platform} is required but download failed!")

    log("\n" + "="*70)
    if success_count >= required_count:
        log("✓ PORTABLE VERACRYPT DOWNLOAD COMPLETE")
        log("="*70)
        log(f"\nDownloaded {success_count} of {len(downloads)} platform(s)")
        log(f"Files saved to: {temp_dir}")
        return temp_dir
    else:
        log("✗ DOWNLOAD FAILED")
        log("="*70)
        log(f"\nOnly {success_count} of {required_count} required downloads succeeded.")
        log("Cannot proceed without portable VeraCrypt binaries.")
        log("\nTroubleshooting:")
        log("  • Check your internet connection")
        log("  • Verify firewall settings")
        log("  • Try again later (download servers may be busy)")
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

    # Download portable VeraCrypt first (so it's ready to copy later)
    veracrypt_dir = None
    if CREATE_DOCS:
        veracrypt_dir = download_portable_veracrypt()

    log("\n" + "="*70)
    log("STEP 1: DRIVE SELECTION")
    log("="*70)
    log("Available storage devices on your system:")
    list_drives()
    log("\nIMPORTANT: Double-check the drive path! All data will be erased.")
    DRIVE = input("Enter the drive to use for USB (e.g., /dev/sda) [Default: /dev/sda]: ") or "/dev/sda"

    confirm = input(f"\nYou have selected {DRIVE}. Is this correct? (y/n) [Default: y]: ") or "y"
    if confirm.lower() != "y":
        log("Drive selection canceled. Exiting.")
        sys.exit(1)

    log("\n" + "="*70)
    log("STEP 2: PREPARING DRIVE")
    log("="*70)
    prepare_drive(DRIVE)

    if CREATE_KALI or CREATE_TAILS or CREATE_DOCS:
        log("\n" + "="*70)
        log("STEP 3: DRIVE WIPING (OPTIONAL)")
        log("="*70)
        log("Wiping destroys all existing data on the drive.")
        log("This prevents recovery of old files and ensures a clean setup.")
        log("")
        if PARANOID_MODE:
            log("PARANOID MODE: 3-pass overwrite (very slow, ~2-3 hours for 64GB)")
        else:
            log("STANDARD MODE: 1-pass zero overwrite (~10-20 min for 64GB)")
        log("Skip wiping if this is already a blank/new drive.")
        log("")

        wipe = input(f"Do you want to wipe {DRIVE} before starting? (y/n) [Default: n]: ") or "n"
        if wipe.lower() == "y":
            if PARANOID_MODE:
                log("\n" + "-"*70)
                log("PARANOID WIPE: 3 passes with random data + final zero pass")
                log("WARNING: This will take HOURS on large drives!")
                log("Estimated time: 2-3 hours for 64GB drive")
                log("-"*70)
                confirm_wipe = input(f"Type 'WIPE' to confirm complete wipe of {DRIVE}: ")
                if confirm_wipe == "WIPE":
                    log("\nClearing partition table and filesystem signatures...")
                    run_command(["sudo", "wipefs", "--all", DRIVE])
                    run_command(["sudo", "sgdisk", "--zap-all", DRIVE])
                    log("\nStarting 3-pass shred (this will take a long time)...")
                    log("Pass 1/3: Random data")
                    log("Pass 2/3: Random data")
                    log("Pass 3/3: Random data")
                    log("Final pass: Zeros")
                    log("You can monitor progress below:")
                    # Paranoid: 3 passes with random data, then zeros
                    run_command(["sudo", "shred", "-vfz", "-n", "3", DRIVE], interactive=True)
                    log(f"\n✓ {DRIVE} securely wiped successfully (paranoid mode).")
                else:
                    log("\nFull wipe canceled. Clearing partition table only...")
                    run_command(["sudo", "wipefs", "--all", DRIVE])
                    run_command(["sudo", "sgdisk", "--zap-all", DRIVE])
                    log("✓ Partition table cleared.")
            else:
                log("\n" + "-"*70)
                log("STANDARD WIPE: Single pass with zeros")
                log("Estimated time: ~10-20 minutes for 64GB drive")
                log("-"*70)
                confirm_wipe = input(f"Type 'WIPE' to confirm wipe of {DRIVE}: ")
                if confirm_wipe == "WIPE":
                    log("\nClearing partition table and filesystem signatures...")
                    run_command(["sudo", "wipefs", "--all", DRIVE])
                    run_command(["sudo", "sgdisk", "--zap-all", DRIVE])
                    log("\nOverwriting entire drive with zeros...")
                    log("Progress will be shown below (this may take 10-20 minutes):")
                    log("(Note: dd will show 'No space left on device' when complete - this is normal)")
                    log("")
                    # Standard: Single pass with zeros (much faster)
                    # Note: dd will report "No space left on device" when it fills the drive - this is expected and means success
                    run_command(["sudo", "dd", "if=/dev/zero", f"of={DRIVE}", "bs=1M", "status=progress", "conv=fdatasync"], interactive=True, ignore_enospc=True)
                    log(f"\n✓ {DRIVE} wiped successfully (standard mode).")
                else:
                    log("\nFull wipe canceled. Clearing partition table only...")
                    run_command(["sudo", "wipefs", "--all", DRIVE])
                    run_command(["sudo", "sgdisk", "--zap-all", DRIVE])
                    log("✓ Partition table cleared.")
        else:
            log("\nSkipping full drive wipe. Clearing partition table only...")
            run_command(["sudo", "wipefs", "--all", DRIVE])
            run_command(["sudo", "sgdisk", "--zap-all", DRIVE])
            log("✓ Partition table cleared.")

    # Initialize variables to track if ISO has been written
    iso_written = False

    if CREATE_KALI or CREATE_TAILS or CREATE_CUSTOM:
        log("\n" + "="*70)
        log("STEP 4: WRITING BOOTABLE ISO")
        log("="*70)
        global KALI_ISO, TAILS_ISO, CUSTOM_ISO
        if CREATE_KALI:
            if not KALI_ISO:
                KALI_ISO = input("Enter the path to the Kali ISO file: ")
            if not os.path.isfile(KALI_ISO):
                log(f"Error: Kali ISO file not found at {KALI_ISO}")
                sys.exit(1)
            ISO_PATH = KALI_ISO
            iso_name = "Kali Linux"
        elif CREATE_TAILS:
            if not TAILS_ISO:
                TAILS_ISO = input("Enter the path to the Tails ISO file: ")
            if not os.path.isfile(TAILS_ISO):
                log(f"Error: Tails ISO file not found at {TAILS_ISO}")
                sys.exit(1)
            ISO_PATH = TAILS_ISO
            iso_name = "Tails"
        elif CREATE_CUSTOM:
            if not CUSTOM_ISO:
                CUSTOM_ISO = input("Enter the path to your custom ISO file: ")
            if not os.path.isfile(CUSTOM_ISO):
                log(f"Error: Custom ISO file not found at {CUSTOM_ISO}")
                sys.exit(1)
            ISO_PATH = CUSTOM_ISO
            iso_name = "Custom"

        # Get ISO size for time estimate
        iso_size_bytes = os.path.getsize(ISO_PATH)
        iso_size_gb = iso_size_bytes / (1024**3)
        estimated_time = int((iso_size_gb / 0.5) * 60)  # Rough estimate: 30 seconds per GB at 50MB/s

        log(f"ISO file: {ISO_PATH}")
        log(f"ISO size: {iso_size_gb:.2f} GB")
        log(f"Estimated write time: ~{estimated_time} seconds ({estimated_time//60} min)")
        log("")

        if CREATE_TAILS:
            # For Tails, flash the ISO to the entire drive without any partitioning
            log(f"Writing {iso_name} ISO to {DRIVE}...")
            log("Progress will be shown below:")
            log("")
            run_command(f"sudo dd if='{ISO_PATH}' of='{DRIVE}' bs=64M status=progress conv=fdatasync", shell=True, interactive=True)
            log(f"\n✓ {iso_name} ISO written to {DRIVE} successfully.")
            iso_written = True
        else:
            # For Kali or Custom ISO, flash and proceed with partition setup
            log(f"Writing {iso_name} ISO to {DRIVE}...")
            log("Progress will be shown below:")
            log("")
            run_command(f"sudo dd if='{ISO_PATH}' of='{DRIVE}' bs=64M status=progress conv=fdatasync", shell=True, interactive=True)
            log(f"\n✓ {iso_name} ISO written to {DRIVE} successfully.")
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
    log("\n" + "="*70)
    log("STEP 5: CREATING PARTITION LAYOUT")
    log("="*70)
    log("Creating 2 partitions:")
    log("  1. Encrypted documents partition (VeraCrypt)")
    log("  2. Tools partition (1GB, unencrypted, contains mount scripts)")
    log("")

    # Clear existing GPT label to start fresh
    log("Creating fresh GPT partition table...")
    run_command(f"sudo parted -a optimal -s {DRIVE} mklabel gpt", shell=True)
    run_command(f"sudo partprobe {DRIVE}", shell=True)
    run_command("sudo udevadm settle", shell=True)
    time.sleep(5)  # Increased sleep to ensure partitions are recognized
    log("✓ GPT partition table created")

    # Get the total size of the drive in bytes
    log("\nCalculating partition sizes...")
    result = subprocess.run(["lsblk", "-b", "-d", "-n", "-o", "SIZE", DRIVE], capture_output=True, text=True)
    try:
        total_size_bytes = int(result.stdout.strip())
    except ValueError:
        log(f"Error: Unable to determine drive size. lsblk output: {result.stdout}")
        sys.exit(1)
    total_size_mib = total_size_bytes / (1024 * 1024)  # Convert to MiB
    total_size_gb = total_size_mib / 1024  # Convert to GiB
    available_gb = (total_size_mib - 1024) / 1024  # Minus 1GB reserved for scripts

    log(f"  Total drive size: {total_size_gb:.2f} GB ({total_size_mib:.0f} MiB)")
    log(f"  Available for documents: {available_gb:.2f} GB (after reserving 1GB for tools)")
    log("")

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
    log(f"\nCreating partition 1 (documents): {(end_docs_mib - start_docs_mib)/1024:.2f} GB...")
    run_command(f"sudo parted -a optimal -s {DRIVE} mkpart primary {start_docs_mib}MiB {end_docs_mib}MiB", shell=True)
    log("✓ Documents partition created")

    # Create unencrypted partition
    start_unencrypted_mib = end_docs_mib
    log(f"Creating partition 2 (tools): ~1 GB...")
    run_command(f"sudo parted -a optimal -s {DRIVE} mkpart primary {start_unencrypted_mib}MiB 100%", shell=True)
    log("✓ Tools partition created")

    # Refresh partition table to recognize new partitions
    log("\nRefreshing partition table...")
    run_command(f"sudo partprobe {DRIVE}", shell=True)
    run_command("sudo udevadm settle", shell=True)
    time.sleep(5)  # Increased sleep to ensure partitions are recognized
    log("✓ Partition table refreshed")

    setup_unencrypted_partition(veracrypt_dir)
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
    setup_unencrypted_partition(veracrypt_dir)

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
    setup_unencrypted_partition(veracrypt_dir)

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
    elif PARANOID_MODE:
        luks_format_cmd = (
            f"sudo cryptsetup luksFormat '{PERSIST_PART}' "
            f"--type luks2 "
            f"--cipher aes-xts-plain64 "
            f"--key-size 512 "
            f"--hash sha512 "
            f"--pbkdf argon2id "
            f"--iter-time 10000 "
            f"--pbkdf-memory 1048576 "
            f"--pbkdf-parallel 4 "
            f"--verify-passphrase"
        )
        mkfs_cmd = f"sudo mkfs.ext4 -L persistence /dev/mapper/kali_USB"
    else:
        luks_format_cmd = (
            f"sudo cryptsetup luksFormat '{PERSIST_PART}' "
            f"--type luks2 "
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

    log("\n" + "="*70)
    log("STEP 6: ENCRYPTING DOCUMENTS PARTITION")
    log("="*70)

    # Check if the partition exists
    if not os.path.exists(DOCS_PART):
        log(f"Error: Partition {DOCS_PART} does not exist.")
        sys.exit(1)

    # Force wipe existing filesystem signatures
    log(f"Preparing partition {DOCS_PART}...")
    run_command(["sudo", "wipefs", "--all", "--force", DOCS_PART])
    log(f"✓ Partition prepared")

    log("\n" + "="*70)
    log("ENCRYPTED VOLUME SETUP")
    log("="*70)
    log("\nYou will now create an encrypted volume for sensitive documents.")
    log("")
    log("SECURITY SETTINGS:")
    log("  • Encryption: AES-Twofish-Serpent (triple cascade)")
    log("  • Hash: SHA-512")
    if PARANOID_MODE:
        log("  • PIM: 5000 (PARANOID mode - maximum security)")
        log("  • Unlock time: ~5-7 seconds")
    else:
        log("  • PIM: 2000 (standard high security)")
        log("  • Unlock time: ~2-3 seconds")
    log("")
    log("PASSWORD REQUIREMENTS:")
    log("  • Minimum 20 characters (longer is better)")
    log("  • Mix uppercase, lowercase, numbers, and symbols")
    log("  • Avoid dictionary words or personal information")
    log("  • Example: My$ecur3Tr@v3lD0cs!2025#Paris")
    log("")
    log("⚠ CRITICAL: There is NO password recovery!")
    log("  If you forget your password, your data is GONE FOREVER.")
    log("")
    log("="*70)
    input("Press ENTER when you're ready to create your password...")

    log("\nConfiguring VeraCrypt encryption for documents partition...")

    # Always use maximum security for documents partition (ignore FAST_MODE)
    # Triple cascade encryption with strongest hash
    pim_value = 5000 if PARANOID_MODE else 2000
    veracrypt_create_cmd = (
        f"veracrypt --text --create '{DOCS_PART}' "
        f"--encryption AES-Twofish-Serpent "
        f"--hash SHA-512 "
        f"--filesystem ext4 "
        f"--volume-type normal "
        f"--pim {pim_value} "  # 2000 standard, 5000 paranoid
    )

    log("\nStarting VeraCrypt encryption (this may take a few minutes)...")
    log("="*70)
    log("VERACRYPT WILL ASK YOU THESE QUESTIONS:")
    log("="*70)
    log("")
    log("1. 'Enter password:' → Type your strong password (20+ characters)")
    log("   Then press ENTER")
    log("")
    log("2. 'Re-enter password:' → Type the SAME password again")
    log("   Then press ENTER")
    log("")
    log("3. 'Enter PIM:' → Just press ENTER")
    log(f"   (We're using PIM {pim_value} automatically)")
    log("")
    log("4. 'Enter keyfile path [none]:' → Just press ENTER")
    log("   (Keyfiles not needed for most users)")
    log("")
    log("5. 'Please type at least 320 randomly chosen characters'")
    log("   → Smash random keys on your keyboard until it says 'Done'")
    log("   This creates entropy for encryption")
    log("")
    log("6. 'Protect hidden volume (if any)? (y=Yes/n=No) [No]:' → Type: n")
    log("   Then press ENTER (we're not using hidden volumes)")
    log("")
    log("="*70)
    log("Creating volume now...")
    log("="*70)
    log("")
    run_command(veracrypt_create_cmd, shell=True, interactive=True)
    log("\n✓ Documents partition encrypted successfully!")
    log(f"  Encryption: AES-Twofish-Serpent (triple cascade)")
    log(f"  Hash: SHA-512")
    log(f"  PIM: {pim_value}")
    log(f"  Filesystem: ext4")

def setup_unencrypted_partition(veracrypt_dir=None):
    """
    Sets up the unencrypted partition for scripts and instructions.

    Args:
        veracrypt_dir (str): Path to directory containing portable VeraCrypt files
    """
    global DRIVE
    UNENCRYPTED_PART = get_partition_name(DRIVE, get_last_partition_number())

    log("\n" + "="*70)
    log("STEP 7: SETTING UP TOOLS PARTITION")
    log("="*70)

    # Check if the partition exists
    if not os.path.exists(UNENCRYPTED_PART):
        log(f"Error: Partition {UNENCRYPTED_PART} does not exist.")
        sys.exit(1)

    log(f"Formatting {UNENCRYPTED_PART} as FAT32...")
    run_command(f"sudo mkfs.vfat -n 'TOOLS' {UNENCRYPTED_PART}", shell=True)
    log("✓ FAT32 filesystem created")

    log("Mounting tools partition...")
    run_command("sudo mkdir -p /mnt/unencrypted", shell=True)
    run_command(f"sudo mount {UNENCRYPTED_PART} /mnt/unencrypted", shell=True)
    log("✓ Tools partition mounted")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tools_dir = os.path.join(script_dir, "tools")

    log("\nCopying helper files from tools/ directory...")

    # Copy README.txt
    readme_path = os.path.join(tools_dir, "README.txt")
    if os.path.exists(readme_path):
        run_command(f"sudo cp '{readme_path}' /mnt/unencrypted/README.txt", shell=True)
        log("  ✓ README.txt copied")
    else:
        log(f"  ⚠ Warning: {readme_path} not found, skipping README")

    # Copy WINDOWS_INSTRUCTIONS.txt
    windows_inst_path = os.path.join(tools_dir, "WINDOWS_INSTRUCTIONS.txt")
    if os.path.exists(windows_inst_path):
        run_command(f"sudo cp '{windows_inst_path}' /mnt/unencrypted/WINDOWS_INSTRUCTIONS.txt", shell=True)
        log("  ✓ WINDOWS_INSTRUCTIONS.txt copied")
    else:
        log(f"  ⚠ Warning: {windows_inst_path} not found")

    # Copy MOBILE_INSTRUCTIONS.txt
    mobile_inst_path = os.path.join(tools_dir, "MOBILE_INSTRUCTIONS.txt")
    if os.path.exists(mobile_inst_path):
        run_command(f"sudo cp '{mobile_inst_path}' /mnt/unencrypted/MOBILE_INSTRUCTIONS.txt", shell=True)
        log("  ✓ MOBILE_INSTRUCTIONS.txt copied")
    else:
        log(f"  ⚠ Warning: {mobile_inst_path} not found")

    # Copy mount_storage.sh
    mount_script_path = os.path.join(tools_dir, "mount_storage.sh")
    if os.path.exists(mount_script_path):
        run_command(f"sudo cp '{mount_script_path}' /mnt/unencrypted/mount_storage.sh", shell=True)
        run_command("sudo chmod +x /mnt/unencrypted/mount_storage.sh", shell=True)
        log("  ✓ mount_storage.sh copied")
    else:
        log(f"  ⚠ Warning: {mount_script_path} not found, skipping mount script")

    # Copy lock_storage.sh
    lock_script_path = os.path.join(tools_dir, "lock_storage.sh")
    if os.path.exists(lock_script_path):
        run_command(f"sudo cp '{lock_script_path}' /mnt/unencrypted/lock_storage.sh", shell=True)
        run_command("sudo chmod +x /mnt/unencrypted/lock_storage.sh", shell=True)
        log("  ✓ lock_storage.sh copied")
    else:
        log(f"  ⚠ Warning: {lock_script_path} not found, skipping lock script")

    # Copy portable VeraCrypt files
    if veracrypt_dir and os.path.exists(veracrypt_dir):
        log("\nCopying portable VeraCrypt binaries...")
        run_command("sudo mkdir -p /mnt/unencrypted/VeraCrypt", shell=True)

        veracrypt_files = [
            ("VeraCrypt-Portable-Windows.exe", "Windows portable"),
            ("VeraCrypt-Portable-Linux.AppImage", "Linux portable AppImage"),
            ("veracrypt-Ubuntu-22.04-amd64.deb", "Linux DEB installer"),
            ("VeraCrypt-MacOS.dmg", "macOS installer")
        ]

        for filename, description in veracrypt_files:
            src = os.path.join(veracrypt_dir, filename)
            if os.path.exists(src):
                run_command(f"sudo cp '{src}' /mnt/unencrypted/VeraCrypt/{filename}", shell=True)
                if "Linux" in filename:
                    run_command(f"sudo chmod +x /mnt/unencrypted/VeraCrypt/{filename}", shell=True)
                log(f"  ✓ {description} copied")
            else:
                log(f"  ⚠ {description} not found (optional)")

        log("  ✓ Portable VeraCrypt binaries installed")
        log("\n  📌 IMPORTANT: These binaries allow accessing encrypted files")
        log("      on ANY Windows, Linux, or Mac computer WITHOUT installing software!")
    else:
        log("\n  ⚠ No portable VeraCrypt binaries provided - skipping")

    log("\nUnmounting tools partition...")
    run_command("sudo umount /mnt/unencrypted", shell=True)
    log("✓ Tools partition setup complete")

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
    parser.add_argument("--paranoid", action="store_true", help="Enable paranoid mode: maximum security, 3-pass shred, highest encryption")
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
    PARANOID_MODE = args.paranoid

    # Paranoid and Fast are mutually exclusive
    if FAST_MODE and PARANOID_MODE:
        log("Error: Cannot use --fast and --paranoid modes together.")
        sys.exit(1)

    if FAST_MODE:
        log("Fast mode enabled: Using less secure encryption for quicker setup.")
    elif PARANOID_MODE:
        log("PARANOID MODE enabled: Maximum security - 3-pass wipe, strongest encryption, highest PIM.")

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

    # Final summary
    log("\n" + "="*70)
    log("SETUP COMPLETE!")
    log("="*70)
    log("")
    log("Your secure storage device is ready!")
    log("")
    log("What was created:")
    if CREATE_KALI:
        log("  ✓ Kali Linux bootable drive")
        log("  ✓ LUKS encrypted persistence partition")
    elif CREATE_TAILS:
        log("  ✓ Tails bootable drive")
    elif CREATE_CUSTOM:
        log("  ✓ Custom bootable drive")
        log("  ✓ LUKS encrypted persistence partition")

    if CREATE_DOCS:
        log("  ✓ VeraCrypt encrypted documents partition")
        if PARANOID_MODE:
            log("    - Triple cascade encryption (AES-Twofish-Serpent)")
            log("    - PIM 5000 (PARANOID mode)")
        else:
            log("    - Triple cascade encryption (AES-Twofish-Serpent)")
            log("    - PIM 2000 (standard security)")
        log("  ✓ Tools partition with helper scripts")
        log("")
        log("Next steps:")
        log("  1. Safely eject the device")
        log("  2. On your target system, mount the TOOLS partition")
        log("  3. Read README.txt for instructions")
        log("  4. Run: sudo ./mount_storage.sh")
        log("")

    log(f"Log file saved: {LOG_FILE}")
    log("="*70)

if __name__ == "__main__":
    main()
