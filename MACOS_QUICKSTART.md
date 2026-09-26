# macOS Quick Start Guide

## Prerequisites

1. **Install Xcode Command Line Tools** (if not installed):
```bash
xcode-select --install
```

2. **Verify Python 3** (usually pre-installed on macOS):
```bash
python3 --version
```

3. **Ensure required tools are available**:
```bash
which networksetup ifconfig tcpdump
```

## Quick Test

### 1. Scan for Networks
```bash
python3 wifisinner_ultimate.py --scan --iface en0
```

Lists nearby WiFi networks. If the `airport` utility is available, it performs a full scan. Otherwise, it lists preferred networks as a fallback.

### 2. Run Environment Detection
```bash
python3 macos_adapter.py --detect --iface en0
```

Checks for debuggers (LLDB/GDB), analysis tools (Frida, Objection, Jadx), and VM indicators.

### 3. Start Basic Operation
```bash
sudo python3 wifisinner_ultimate.py --iface en0
```

On macOS, this runs in compatibility mode:
- Scans for nearby networks (or lists preferred networks if `airport` utility is unavailable)
- Starts an OTA delivery server on port 8080
- Starts probe request sniffer
- Runs Phase 2-4 modules (designed for Android targets, limited functionality on macOS)

## Interface Selection

macOS typically uses:
- `en0` - Built-in WiFi (most common)
- `en1` - External WiFi adapter

Check your interface:
```bash
networksetup -listallhardwareports
```

## Limitations on macOS

### What Works ✅
- Network scanning
- Probe request sniffing
- OTA payload delivery
- Environment detection
- Persistence (LaunchAgent)

### What's Limited ⚠️
- **Beacon Spoofing**: Not available (no raw 802.11 frame injection)
- **Monitor Mode**: Not available on macOS
- **Deauth Hammering**: Not available (requires raw 802.11 frames)
- **Privilege Escalation**: Phase 2 modules target Android, not macOS
- **Android Integration**: Requires Android emulator or ADB

## Troubleshooting

### "Permission denied" errors
```bash
sudo python3 wifisinner_ultimate.py --iface en0
```

### "No WiFi interface found"
```bash
# Check available interfaces
networksetup -listallhardwareports

# Try en1 if en0 doesn't work
sudo python3 wifisinner_ultimate.py --iface en1
```

### OTA server port conflict
```bash
# If port 8080 is in use, the server will try 0.0.0.0 and 127.0.0.1
# Check for conflicts:
lsof -i :8080
```

### Airport utility missing
The `airport` utility is optional. If not available, the scanner falls back to listing preferred networks.

To install the airport utility:
```bash
# Create symlink to airport (if available on your system)
sudo ln -s "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport" /usr/local/bin/airport
```

### tcpdump not found
```bash
# Install via Homebrew
brew install tcpdump
```

## Comparison: macOS vs Linux

| Feature | Linux | macOS |
|---------|-------|-------|
| WiFi Control | Full (nmcli, iw) | Limited (networksetup) |
| Monitor Mode | ✅ Yes | ❌ No |
| Beacon Spoofing | Full control | ❌ Not available |
| Deauth | Raw 802.11 frames | ❌ Not available |
| Privilege Escalation | Dirty COW, etc. | Android-only phases |
| Android Integration | Direct ADB | Emulator required |

## Advanced: Using with Android Emulator

To test the full weapon system on macOS:

1. **Install Android Studio**
```bash
brew install --cask android-studio
```

2. **Create AVD (Android Virtual Device)**
```bash
# Open Android Studio → AVD Manager
# Create device with Android 10+
```

3. **Connect to same WiFi**
- Both Mac and emulator on same network
- Get emulator IP: `adb shell ip route`

4. **Run macOS adapter**
```bash
sudo python3 wifisinner_ultimate.py --iface en0
```

5. **Point emulator to Mac**
- Configure emulator WiFi to use Mac as gateway
- Or use ADB port forwarding

## Performance Tips

1. **Use built-in WiFi**: External adapters may not work well
2. **Close other apps**: WiFi scanning can be intensive
3. **Disable SIP** (optional): For deeper system access
   ```bash
   # In Recovery Mode: csrutil disable
   ```
4. **Use Terminal.app**: iTerm2 may have permission issues

## Logging

All logs are written to:
- `/tmp/wifisinner.log` (macOS persistence)
- `loot/YYYYMMDD_HHMMSS/` (capture data)

## Next Steps

1. **Test with Linux VM**: For full capabilities
2. **Use Boot Camp**: Native Windows/Linux on Mac hardware
3. **External WiFi Adapter**: Some work in monitor mode on macOS
4. **Combine with Linux**: Use Mac for C2, Linux for access

## Support

For macOS-specific issues:
- Check `macos_adapter.py` implementation
- Verify interface permissions: `sudo diskutil list`
- Check system logs: `log show --predicate 'process == "airport"' --last 5m`

---

**Note**: macOS compatibility mode is designed for development and testing. For production operations, use Linux for full capabilities.
