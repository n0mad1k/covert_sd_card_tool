======================================================================
              SECURE STORAGE - QUICK START GUIDE
======================================================================

WHAT'S ON THIS DEVICE:
  • Encrypted storage partition for sensitive documents
  • Portable VeraCrypt (works on ANY computer - no installation!)
  • Helper scripts (Linux/Mac)
  • Instructions for Windows and mobile devices

======================================================================
ACCESSING YOUR FILES - QUICK GUIDE
======================================================================

LINUX / MAC:
  1. Open terminal in this folder
  2. Run: sudo ./mount_storage.sh
  3. Enter your password
  4. Files appear in: ~/SecureStorage

WINDOWS:
  1. Open "WINDOWS_INSTRUCTIONS.txt" on this device
  2. Follow the step-by-step guide
  3. Use portable VeraCrypt from "VeraCrypt" folder (no install needed!)

ANDROID:
  1. Install "EDS Lite" from Google Play Store (FREE)
     https://play.google.com/store/apps/details?id=com.sovworks.projecteds
  2. Connect USB with OTG adapter
  3. Open "MOBILE_INSTRUCTIONS.txt" for step-by-step guide

iOS (iPhone/iPad):
  1. Install "Crypto Disks" from App Store (~$4.99)
     https://apps.apple.com/us/app/crypto-disks-store-private/id889549308
  2. See "MOBILE_INSTRUCTIONS.txt" for setup
  ⚠ iOS has limitations - requires copying files, can't mount USB directly

======================================================================
IMPORTANT: HOW TO SAFELY LOCK YOUR STORAGE
======================================================================

LINUX / MAC:
  1. Close ALL programs using the secure storage
  2. Run: sudo ./lock_storage.sh
  3. Wait for "SUCCESS" message
  4. Safe to remove device

WINDOWS:
  1. Close all files
  2. In VeraCrypt, select the drive
  3. Click "Dismount"
  4. Use "Safely Remove Hardware"

⚠ CRITICAL: ALWAYS lock/dismount before removing!
   Otherwise you risk losing your data.

======================================================================
PORTABLE VERACRYPT - NO INSTALLATION REQUIRED!
======================================================================

Inside the "VeraCrypt" folder on this device:

• VeraCrypt-Portable-Windows.exe
    → Double-click to run on ANY Windows PC
    → Works without admin rights on most systems

• VeraCrypt-Portable-Linux.AppImage
    → Run on ANY Linux system (no install!)
    → Command: ./VeraCrypt-Portable-Linux.AppImage
    → AppImage = portable, works on all Linux distributions

• veracrypt-Ubuntu-22.04-amd64.deb
    → System-wide installer for Ubuntu/Debian
    → Install with: sudo dpkg -i veracrypt-Ubuntu-22.04-amd64.deb
    → Use this if you prefer installed version over AppImage

• VeraCrypt-MacOS.dmg
    → Install on Mac (one-time)
    → Works on any Mac after that

This means you can access your encrypted files on ANY computer
even if VeraCrypt is not installed!

======================================================================
YOUR PASSWORD
======================================================================

⚠ There is NO password recovery! If you forget it, data is GONE.

Password details:
  • Case-sensitive (Abc123 ≠ abc123)
  • Minimum 20 characters recommended
  • Mix of letters, numbers, symbols
  • Write it down and keep it SAFE (not on this device!)

If you set a PIM value:
  • Standard setup: PIM = 2000
  • Paranoid setup: PIM = 5000
  • VeraCrypt will ask for this when mounting

======================================================================
TROUBLESHOOTING
======================================================================

PROBLEM: "Cannot find TOOLS partition"
FIX: Ensure device is fully connected; try different USB port

PROBLEM: "Wrong password" (but you know it's correct)
FIX: Check if CAPS LOCK is on; verify PIM value

PROBLEM: "Volume already mounted"
FIX: Close any VeraCrypt windows and run:
     • Linux/Mac: sudo veracrypt -d
     • Windows: Dismount all in VeraCrypt

PROBLEM: "Permission denied" when accessing files
FIX:
     • Linux/Mac: Re-run mount script (it sets permissions)
     • Windows: Check if you ran VeraCrypt as administrator

PROBLEM: "Files appear but I can't edit them"
FIX:
     • Linux/Mac: Run: sudo chown -R $USER ~/SecureStorage
     • Windows: Right-click → Properties → Security → Edit

PROBLEM: Device not detected on Android
FIX:
     • Check USB OTG adapter is working
     • Enable "File Transfer" mode in USB settings
     • Try different OTG adapter

======================================================================
FILE LOCATIONS AFTER MOUNTING
======================================================================

Linux/Mac:     ~/SecureStorage
               (In your home folder)

Windows:       Z:\ (or whatever drive letter you selected)
               Shows in "This PC"

Android:       Accessible within EDS Lite or VeraCrypt app

======================================================================
SECURITY NOTES
======================================================================

✓ Your files use military-grade encryption
✓ AES-Twofish-Serpent triple cascade (strongest available)
✓ Even supercomputers cannot crack this encryption

⚠ The password is the ONLY key
⚠ No backdoors, no recovery, no "forgot password" option
⚠ Keep password safe but separate from this device

Best practices:
  • Always dismount before removing device
  • Don't leave mounted when unattended
  • Use strong unique password
  • Don't store password on this device
  • Lock your computer when storage is mounted

======================================================================
ADVANCED: MANUAL MOUNTING (if scripts fail)
======================================================================

LINUX/MAC:
  1. Find encrypted partition:
       lsblk -o NAME,SIZE,LABEL,FSTYPE
       (Look for partition WITHOUT filesystem label)

  2. Mount with VeraCrypt:
       sudo veracrypt /dev/sdX2 ~/SecureStorage
       (Replace sdX2 with your partition)

  3. Enter password and PIM when prompted

WINDOWS:
  1. Open portable VeraCrypt
  2. Select any drive letter
  3. Click "Select Device"
  4. Choose partition WITHOUT label (not the TOOLS one)
  5. Click "Mount"
  6. Enter password

======================================================================
NEED MORE HELP?
======================================================================

• Windows users: See WINDOWS_INSTRUCTIONS.txt
• Mobile users: See MOBILE_INSTRUCTIONS.txt
• VeraCrypt documentation: https://www.veracrypt.fr/en/Documentation.html

======================================================================
