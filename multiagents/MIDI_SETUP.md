# MIDI Library Setup Guide

## Problem: AttributeError: module 'rtmidi' has no attribute 'API_UNSPECIFIED'

This error occurs when there's a version mismatch or incorrect MIDI library installation.

## Solution

### Step 1: Uninstall conflicting packages

```bash
pip uninstall rtmidi-python rtmidi python-rtmidi -y
```

### Step 2: Install correct packages

```bash
pip install mido python-rtmidi
```

### Step 3: Verify installation

```python
import mido
import rtmidi

# Check if API_UNSPECIFIED exists
print(hasattr(rtmidi, 'API_UNSPECIFIED'))  # Should print True

# Test mido
print(mido.get_input_names())  # Should list available MIDI ports
```

## Alternative: Use PortMidi backend (macOS)

If `python-rtmidi` doesn't work on your system, you can use PortMidi backend:

```bash
pip install mido python-rtmidi
# On macOS, you might also need:
# brew install portmidi
```

## Troubleshooting

### Windows
- Make sure you have the correct `python-rtmidi` package (not `rtmidi-python`)
- If issues persist, try: `pip install --upgrade python-rtmidi mido`

### Linux
- You may need system libraries: `sudo apt-get install libasound2-dev libjack-dev`
- Then: `pip install python-rtmidi mido`

### macOS
- PortMidi backend is usually more reliable
- Install: `brew install portmidi`
- Then: `pip install mido python-rtmidi`

## Check your current installation

```bash
pip list | grep -i midi
pip show python-rtmidi
pip show mido
```

## Quick Fix Script

Run this Python script to check and fix:

```python
import sys
import subprocess

def check_and_fix_midi():
    try:
        import mido
        import rtmidi
        if hasattr(rtmidi, 'API_UNSPECIFIED'):
            print("✓ MIDI libraries are correctly installed")
            return True
        else:
            print("✗ rtmidi version incompatible")
    except ImportError:
        print("✗ MIDI libraries not installed")
    
    print("\nAttempting to fix...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "rtmidi-python", "rtmidi"])
    subprocess.run([sys.executable, "-m", "pip", "install", "mido", "python-rtmidi"])
    print("\nPlease restart Python and try again")

if __name__ == "__main__":
    check_and_fix_midi()
```

