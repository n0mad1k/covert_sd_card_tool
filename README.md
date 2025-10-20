# Covert SD Card Tool

## Introduction

The **Covert SD Card Tool** is a Python script designed to automate the process of setting up a bootable USB/SD card with either Kali Linux or Tails OS. It includes options to create encrypted persistence partitions, secure document storage, and user-friendly access scripts. This tool simplifies the complex steps involved in preparing a secure, portable operating system on a USB drive or SD card.

## Features

- **Install Kali Linux or Tails OS** on a USB/SD card
- **Create an encrypted persistence partition** for Kali Linux (LUKS encryption)
- **Create a maximum-security encrypted documents partition** with triple-cascade encryption
- **Secure drive wiping** using multi-pass shred for data sanitization
- **User-friendly access scripts** for mounting and locking secure storage
- **OPSEC-focused design** - generated scripts use generic terminology
- **Automated dependency checking and installation**

## Prerequisites

- **Operating System:** Linux (Debian-based distributions recommended)
- **Python Version:** Python 3.x
- **Root Access:** Required for disk operations
- **Dependencies:**
  - `parted` - Partition management
  - `cryptsetup` - LUKS encryption
  - `lsblk` - Block device listing
  - `dd` - Disk writing
  - `sgdisk` - GPT partition manipulation
  - `wipefs` - Filesystem signature removal
  - `shred` - Secure data wiping
  - `bc` - Calculator for partition math
  - `fdisk` - Partition table manipulation
  - `veracrypt` - Document partition encryption
  - `lsof`, `fuser` - Process detection
  - `udevadm` - Device management

**Note:** The script will automatically detect missing dependencies and offer to install them.

## Installation

1. **Clone the Repository or Download the Script:**

   ```bash
   git clone https://github.com/yourusername/covert_sd_card_tool.git
   cd covert_sd_card_tool
   ```

2. **Make the Script Executable:**

   ```bash
   chmod +x covert_sd_card_tool.py
   ```

## Usage

Run the script with appropriate options:

```bash
sudo ./covert_sd_card_tool.py [options]
```

### Command-Line Options

- `-a`, `--all` : Set up both the OS bootable USB and the documents partition (defaults to Kali)
- `-k`, `--kali` : Create a Kali bootable USB and persistence partition
- `-t`, `--tails` : Create a Tails bootable USB (no persistence, mutually exclusive with `-a`)
- `-c`, `--custom` : Create a custom ISO bootable USB (uses Kali-style partitioning with persistence)
- `-d`, `--docs` : Create an encrypted documents partition
- `-i`, `--iso` : Path to the ISO file (Kali, Tails, or custom)
- `--fast` : Enable fast setup mode (weaker encryption, faster setup - not recommended)
- `--paranoid` : Enable paranoid mode (maximum security: 3-pass wipe, Argon2id, PIM 5000)
- `--debug` : Enable debug mode with verbose logging

**Note:** `--fast` and `--paranoid` are mutually exclusive. Documents partition always uses strong encryption even in fast mode.

### Examples

- **Install Kali with Encrypted Persistence and Encrypted Documents Partition:**

  ```bash
  sudo ./covert_sd_card_tool.py -a -i /path/to/kali.iso
  ```

- **Install Tails with Encrypted Documents Partition:**

  ```bash
  sudo ./covert_sd_card_tool.py -t -d -i /path/to/tails.iso
  ```

- **Install Tails Only (No Documents Partition):**

  ```bash
  sudo ./covert_sd_card_tool.py -t -i /path/to/tails.iso
  ```

- **Create Encrypted Documents Partition Only (No OS):**

  ```bash
  sudo ./covert_sd_card_tool.py -d
  ```

- **Install Custom ISO (e.g., Parrot OS, BlackArch) with Persistence and Documents:**

  ```bash
  sudo ./covert_sd_card_tool.py -c -d -i /path/to/custom.iso
  ```

- **Install Custom ISO with Persistence Only (No Documents):**

  ```bash
  sudo ./covert_sd_card_tool.py -c -i /path/to/custom.iso
  ```

- **Paranoid Mode - Maximum Security (Tails + Docs):**

  ```bash
  sudo ./covert_sd_card_tool.py -t -d -i /path/to/tails.iso --paranoid
  ```

## Security Features

### Documents Partition Encryption

The documents partition uses **strong security** in all modes:

**Standard Mode (default):**
- **Triple Cascade Encryption:** AES-Twofish-Serpent (3 layers)
- **Hash Algorithm:** SHA-512
- **Key Derivation:** PIM 2000 (strong key stretching)
- **Unlock Time:** ~2-3 seconds
- **Filesystem:** ext4
- **Full Format:** Always overwrites old data

**Paranoid Mode (`--paranoid`):**
- **Triple Cascade Encryption:** AES-Twofish-Serpent (3 layers)
- **Hash Algorithm:** SHA-512
- **Key Derivation:** PIM 5000 (maximum key stretching)
- **Unlock Time:** ~5-7 seconds
- **Security:** Would take trillions of years to brute force

**Fast Mode (`--fast`):**
- Documents still use standard mode (PIM 2000) - no compromise on docs security

### Persistence Partition Encryption (Kali/Custom)

**Standard Mode (default):**
- **Algorithm:** AES-XTS-PLAIN64
- **Key Size:** 512-bit
- **Hash:** SHA-512
- **KDF:** LUKS2 PBKDF2
- **Iteration Time:** 5 seconds

**Paranoid Mode (`--paranoid`):**
- **Algorithm:** AES-XTS-PLAIN64
- **Key Size:** 512-bit
- **Hash:** SHA-512
- **KDF:** LUKS2 Argon2id (memory-hard, GPU-resistant)
- **Memory:** 1GB
- **Parallel Threads:** 4
- **Iteration Time:** 10 seconds

**Fast Mode (`--fast`):**
- **Algorithm:** AES-CBC-ESSIV:SHA256
- **Key Size:** 256-bit
- **Hash:** SHA-256
- **KDF:** LUKS1 PBKDF2
- **Iteration Time:** 1 second

### Secure Drive Wiping

**Standard Mode (default):**
- **1 pass** with zeros (`dd if=/dev/zero`)
- Fast and sufficient for most use cases
- Prevents casual data recovery
- Confirmation required (must type 'WIPE')

**Paranoid Mode (`--paranoid`):**
- **3 passes** with random data (`shred`)
- **Final pass** with zeros
- Makes data recovery virtually impossible
- Defense against forensic recovery techniques
- **Much slower** (can take hours on large drives)
- Confirmation required (must type 'WIPE')

### OPSEC (Operational Security)

The generated helper scripts use **generic terminology** to avoid disclosing encryption methods:

- Scripts renamed to `mount_storage.sh` and `lock_storage.sh` (instead of mentioning encryption types)
- README uses terms like "secure storage" instead of specific encryption names
- No algorithm disclosure in user-facing documentation on the device
- Suitable for travel scenarios where device inspection may occur

## Generated Helper Scripts

The tool creates a small unencrypted partition (TOOLS) containing:

### `mount_storage.sh`
- Interactive script to mount the encrypted documents partition
- Shows available devices and validates input
- Mounts to `/mnt/secure_storage`
- Clear error messages and success confirmations

### `lock_storage.sh`
- Safely dismounts and locks the encrypted storage
- Checks for open files before locking
- Shows warnings if applications are still using the storage
- Syncs pending writes before dismount
- Prevents data loss from improper ejection

### `README.txt`
- Simple instructions for non-technical users
- Generic terminology (no encryption disclosure)
- Step-by-step mount/lock procedures

## Security Mode Comparison

| Feature | Fast Mode | Standard Mode (Default) | Paranoid Mode |
|---------|-----------|------------------------|---------------|
| **Drive Wipe** | Partition table clear only | 1-pass zeros | 3-pass shred + zeros |
| **Wipe Time (64GB)** | Instant | ~5-10 min | ~2-3 hours |
| **Persistence KDF** | LUKS1 PBKDF2 | LUKS2 PBKDF2 | LUKS2 Argon2id |
| **Persistence Unlock** | ~1 sec | ~5 sec | ~10 sec |
| **Docs Encryption** | AES-Twofish-Serpent | AES-Twofish-Serpent | AES-Twofish-Serpent |
| **Docs PIM** | 2000 | 2000 | 5000 |
| **Docs Unlock** | ~2-3 sec | ~2-3 sec | ~5-7 sec |
| **Best For** | Testing/dev | Travel, daily use | Maximum security, high-value targets |

**Recommendation:** Use **standard mode** for most cases. Use **paranoid mode** if:
- You're protecting extremely sensitive data
- You face nation-state level threats
- You have time for longer setup and unlock times
- You want defense against forensic analysis

## Important Security Notes

⚠️ **Password Strength:** Use strong passphrases (20+ characters, mixed case, numbers, symbols)

⚠️ **No Password Recovery:** If you forget your password, your data is **permanently inaccessible**

⚠️ **PIM Value:** The tool enforces PIM 2000 for documents partition - this adds 2-3 seconds to unlock time but massively increases security

⚠️ **Always Lock Before Removal:** Use `lock_storage.sh` before removing the device to prevent data corruption

⚠️ **Fast Mode:** While available for persistence partition, documents partition **always uses maximum security**

## Partition Layout Examples

### Kali + Documents (`-a`)
1. **Partition 1:** Kali Live OS (bootable)
2. **Partition 2:** LUKS encrypted persistence (configurable size, e.g., 4GB)
3. **Partition 3:** VeraCrypt encrypted documents (remaining space minus 1GB)
4. **Partition 4:** Unencrypted tools partition (1GB, FAT32, contains scripts)

### Tails Only (`-t`)
- **Entire Drive:** Tails Live OS (bootable, no additional partitions)

### Tails + Documents (`-t -d`)
1. **Partition 1:** Tails Live OS (bootable, 12MB EFI System)
2. **Partition 2:** Tails system partition (~2-3GB depending on Tails version)
3. **Partition 3:** VeraCrypt encrypted documents (remaining space minus 1GB)
4. **Partition 4:** Unencrypted tools partition (1GB, FAT32, contains scripts)

### Documents Only (`-d`)
1. **Partition 1:** VeraCrypt encrypted documents (remaining space minus 1GB)
2. **Partition 2:** Unencrypted tools partition (1GB, FAT32, contains scripts)

### Custom ISO + Documents (`-c -d`)
1. **Partition 1:** Custom Live OS (bootable)
2. **Partition 2:** LUKS encrypted persistence (configurable size, e.g., 4GB)
3. **Partition 3:** VeraCrypt encrypted documents (remaining space minus 1GB)
4. **Partition 4:** Unencrypted tools partition (1GB, FAT32, contains scripts)

**Note:** Custom ISO mode uses Kali-style partitioning. Works well with Debian-based live ISOs like Parrot OS, BlackArch, BackBox, etc.

## Using Custom ISOs

The `-c` (custom) flag allows you to use **any bootable ISO** and set it up with encrypted persistence and documents partitions. This is useful for:

### Compatible ISOs
- **Parrot Security OS** - Privacy-focused security distro
- **BlackArch Linux** - Penetration testing distro
- **BackBox** - Ubuntu-based penetration testing
- **Pentoo** - Gentoo-based security distro
- **Any Debian/Ubuntu-based live ISO**

### How It Works
Custom ISOs are treated like Kali Linux:
1. ISO is flashed to the drive
2. LUKS encrypted persistence partition is created (if you want settings to persist)
3. VeraCrypt encrypted documents partition is added (if `-d` flag is used)
4. Tools partition with mount/lock scripts

### Example: Parrot OS with Docs
```bash
sudo ./covert_sd_card_tool.py -c -d -i ~/Downloads/parrot-security.iso
```

### Compatibility Notes
- **Best for:** Debian/Ubuntu-based live ISOs
- **May not work with:** Arch-based ISOs (different partition structure), Windows ISOs
- **Persistence:** Depends on the ISO supporting LUKS persistence (Debian-based usually do)
- If persistence doesn't work with your ISO, you can still use the documents partition

## Troubleshooting

### Device Busy Errors
- The tool automatically unmounts partitions and kills processes using the drive
- If problems persist, manually unmount: `sudo umount /dev/sdX*`
- Check for processes: `sudo lsof /dev/sdX`

### VeraCrypt Not Found
- On Debian/Ubuntu: `sudo apt install veracrypt`
- Or the script will offer to install it automatically

### Permission Denied
- Always run with `sudo`
- Ensure your user has sudo privileges

### Drive Not Detected
- Check if drive is connected: `lsblk`
- Verify drive path (e.g., `/dev/sdb` not `/dev/sdb1`)
- Try unplugging and reconnecting the device

## License

This tool is provided as-is for educational and legitimate security purposes only. Use responsibly and in compliance with applicable laws.

## Contributing

Contributions, bug reports, and feature requests are welcome! Please open an issue or submit a pull request.

## Disclaimer

This tool performs destructive operations on storage devices. **Always verify you've selected the correct drive** before proceeding. The authors are not responsible for data loss.