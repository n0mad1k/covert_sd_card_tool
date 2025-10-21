# Portable VeraCrypt Setup Instructions

Before running the main tool, you need to download portable VeraCrypt binaries.
These will be copied to the TOOLS partition so the device works on any computer.

## Required Downloads

Download the following files and place them in this directory (`tools/veracrypt/`):

### 1. Windows Portable (REQUIRED)
- **File**: `VeraCrypt Portable.exe`
- **URL**: https://www.veracrypt.fr/en/Downloads.html
- **Section**: "Portable" under Windows
- **Size**: ~30 MB
- **Rename to**: `VeraCrypt-Portable-Windows.exe`

### 2. Linux Portable (REQUIRED)
- **Option A - GUI version**:
  - Download from: https://www.veracrypt.fr/en/Downloads.html
  - Generic Installer: `veracrypt-*-setup.tar.bz2`
  - Extract and place: `veracrypt-*-setup-gui-x64`
  - **Rename to**: `VeraCrypt-Portable-Linux`

- **Option B - Console only**:
  - Download: `veracrypt-*-setup-console-x64`
  - **Rename to**: `VeraCrypt-Portable-Linux-Console`

### 3. macOS Portable (OPTIONAL)
- **File**: `VeraCrypt_*.dmg`
- **URL**: https://www.veracrypt.fr/en/Downloads.html
- **Note**: Not truly "portable" but can be included for reference
- **Rename to**: `VeraCrypt-MacOS.dmg`

### 4. Android APK (OPTIONAL but recommended)
- **Source**: https://github.com/veracrypt/VeraCrypt/releases
- **Alternative**: EDS Lite from Play Store (can't include, user must download)
- **Note**: Android apps can't be "portable" but having APK helps

## Quick Download Script

Run this to download automatically (Linux):

```bash
cd tools/veracrypt/

# Windows Portable
wget https://launchpad.net/veracrypt/trunk/1.26.7/+download/VeraCrypt_Portable_1.26.7.exe \
  -O VeraCrypt-Portable-Windows.exe

# Linux Console
wget https://launchpad.net/veracrypt/trunk/1.26.7/+download/veracrypt-console-1.26.7-Ubuntu-22.04-amd64.deb \
  -O veracrypt-linux.deb
ar x veracrypt-linux.deb
tar xf data.tar.xz
cp usr/bin/veracrypt VeraCrypt-Portable-Linux
chmod +x VeraCrypt-Portable-Linux
rm -rf usr/ *.tar.* *.deb

# macOS
wget https://launchpad.net/veracrypt/trunk/1.26.7/+download/VeraCrypt_1.26.7.dmg \
  -O VeraCrypt-MacOS.dmg

echo "✓ Downloads complete!"
```

## Verification

After downloading, your `tools/veracrypt/` directory should contain:

```
tools/veracrypt/
├── DOWNLOAD_INSTRUCTIONS.md (this file)
├── VeraCrypt-Portable-Windows.exe  (~30 MB)
├── VeraCrypt-Portable-Linux        (~3-5 MB)
└── VeraCrypt-MacOS.dmg             (~40 MB) [optional]
```

## Notes

- **Total size**: ~70-80 MB for all platforms
- **License**: VeraCrypt is open source (Apache 2.0 / TrueCrypt License 3.0)
- **Updates**: Check veracrypt.fr periodically for newer versions
- These portable versions allow accessing your encrypted partition on ANY computer without installing software

## After Downloading

Once you have the files in place, run the main setup script:

```bash
sudo python3 covert_sd_card_tool.py -d /dev/sdX -a -t /path/to/tails.iso
```

The script will automatically copy these portable versions to the TOOLS partition.
