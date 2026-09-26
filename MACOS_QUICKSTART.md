# macOS Quick Start Guide

## Prerequisites

1. **Install Xcode Command Line Tools** (if not installed):
```bash
xcode-select --install
```

2. **Install Python 3** (usually pre-installed on macOS):
```bash
python3 --version
```

3. **Install scapy** (for packet capture):
```bash
sudo python3 -m pip install scapy
```

## Quick Test

### 1. Scan for Networks
```bash
python3 wifisinner_ultimate.py --scan --iface en0
```

This will list all nearby WiFi networks using macOS's native WiFi stack.

### 2. Run Environment Detection
```bash
python3 macos_adapter.py --detect --iface en0
```

Checks for debuggers, analysis tools, and VM indicators.

### 3. Start Basic Operation
```bash
sudo python3 wifisinner_ultimate.py --iface en0
```

On macOS, this will:
- Scan for probe requests
- Start an OTA delivery server
- Capture basic device information

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
- C2 tunneling
- Self-destruct

### What's Limited ⚠️
- **Beacon Spoofing**: Uses Internet Sharing API (less control)
- **Monitor Mode**: Not available (no raw 802.11 frames)
- **Deauth Hammering**: Limited (uses ARP spoofing instead)
- **Privilege Escalation**: Requires specific macOS versions
- **Android Integration**: Needs Android emulator or ADB

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

### "Scapy not found"
```bash
sudo python3 -m pip install scapy
```

### Airport utility missing
```bash
# Create symlink to airport
sudo ln -s "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport" /usr/local/bin/airport
```

## Comparison: macOS vs Linux

| Feature | Linux | macOS |
|---------|-------|-------|
| WiFi Control | Full (nmcli, iw) | Limited (networksetup) |
| Monitor Mode | ✅ Yes | ❌ No |
| Beacon Spoofing | Full control | Internet Sharing API |
| Deauth | Raw 802.11 frames | ARP spoofing |
| Privilege Escalation | Dirty COW, etc. | Kernel patches |
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
