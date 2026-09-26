# WIFISINNER ULTIMATE - Clean UI Guide

## UI Modes

### Clean Mode (Default)
```bash
sudo python3 wifisinner_clean.py --ui clean
```
- Animated spinner
- Organized sections
- Status indicators
- Minimal scrolling

### Quiet Mode
```bash
sudo python3 wifisinner_clean.py --ui quiet
```
- Compact output
- No animations
- Quick status updates
- Less verbose

### Verbose Mode
```bash
sudo python3 wifisinner_ultimate.py --ui verbose
```
- Full detailed output
- All debug information
- Original style

## New Commands

### Scan Networks (Clean UI)
```bash
sudo python3 wifisinner_clean.py --scan --iface en0
```

**Output:**
```
═══ WIFISINNER ULTIMATE ═══
Platform: Darwin

▸ Found 104 networks:
  • networksetup -listnetworkserviceorder
  • networksetup -listallnetworkservices
  ...

✓ Phase 1 complete
```

### Run with Clean UI
```bash
sudo python3 wifisinner_clean.py --iface en0
```

**Output:**
```
═══════════════════════════════
WIFISINNER ULTIMATE
Platform: Darwin
═══════════════════════════════

[PHASE 1] Autonomous Access Acquisition
  [1] Scanning networks...
  ✓ Found 104 networks
  [2] Starting OTA server...
  [3] Starting probe sniffer...
  ⚠ Full beacon spoofing limited on macOS

✓ Phase 1 complete
...
```

## Visual Indicators

| Icon | Meaning |
|------|---------|
| ✓ | Success |
| ⚠ | Warning |
| ✗ | Error |
| • | List item |
| ⠋ | Loading |

## Color Coding

| Color | Meaning |
|-------|---------|
| 🟢 Green | Success |
| 🟡 Yellow | Warning |
| 🔴 Red | Error |
| 🔵 Cyan | Info |
| 🟣 Magenta | Headers |

## Tips

1. **Use `--ui quiet`** for scripting
2. **Use `--ui clean`** for interactive use
3. **Use `--scan`** to quickly check nearby networks
4. **Use `--dry-run`** to see configuration

## Comparison

### Old Style (Verbose)
```
[1.1] macOS mode: Scanning networks...
[+] Found 104 networks
     networksetup -listnetworkserviceorder
     networksetup -listallnetworkservices
     ...
[1.2] macOS mode: Starting OTA server...
[macOS OTA] Server failed: [Errno 49] Can't assign requested address
[1.3] macOS mode: Starting probe sniffer...
[!] macOS: Full beacon spoofing limited. Use Linux for complete features.
```

### New Clean UI
```
[PHASE 1] Autonomous Access Acquisition
  [1] Scanning networks...
  ✓ Found 104 networks
  [2] Starting OTA server...
  [3] Starting probe sniffer...
  ⚠ Full beacon spoofing limited on macOS
```

## Examples

### Quick Scan
```bash
sudo python3 wifisinner_clean.py --scan --iface en0 --ui clean
```

### Full Operation (Quiet)
```bash
sudo python3 wifisinner_clean.py --iface en0 --ui quiet
```

### Full Operation (Clean)
```bash
sudo python3 wifisinner_clean.py --iface en0 --ui clean
```

### Dry Run
```bash
sudo python3 wifisinner_clean.py --dry-run --ui clean
```
```

