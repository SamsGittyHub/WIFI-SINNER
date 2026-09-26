#!/usr/bin/env python3
"""
WIFISINNER ULTIMATE - Clean Terminal UI

User-friendly interface with progress indicators, collapsible sections,
and organized output.
"""

import os
import sys
import threading
import time
from datetime import datetime


# Colors
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


class TerminalUI:
    """Clean terminal user interface"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.columns = os.get_terminal_size().columns - 2
        self.sections = {}
        self.running = False
        self.spinner_idx = 0
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def start(self):
        """Start UI update loop"""
        self.running = True
        self.spinner_thread = threading.Thread(target=self._spinner_loop, daemon=True)
        self.spinner_thread.start()
    
    def stop(self):
        """Stop UI"""
        self.running = False
        print(f"\n{C_RESET}", end="")
        sys.stdout.flush()
    
    def _spinner_loop(self):
        """Update spinner animation"""
        while self.running:
            time.sleep(0.1)
            self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
    
    def get_spinner(self):
        """Get current spinner character"""
        return self.spinner_chars[self.spinner_idx]
    
    def clear_line(self):
        """Clear current line"""
        print(f"\r{C_DIM}{' ' * self.columns}{C_RESET}", end="\r")
    
    def header(self, title, subtitle=None):
        """Display main header"""
        self.clear_line()
        print(f"\n{C_BMAGENTA}{'═' * min(70, self.columns)}{C_RESET}")
        print(f"{C_BMAGENTA}WIFISINNER ULTIMATE{C_RESET} — Pegasus-Grade Mobile Financial Weapon")
        if subtitle:
            print(f"{C_DIM}{subtitle}{C_RESET}")
        print(f"{C_BMAGENTA}{'═' * min(70, self.columns)}{C_RESET}\n")
        sys.stdout.flush()
    
    def phase_start(self, phase_num, phase_name):
        """Display phase header"""
        self.clear_line()
        print(f"\n{C_BCYAN}[PHASE {phase_num}]{C_RESET} {phase_name}")
        print(f"{C_DIM}{'─' * min(60, self.columns)}{C_RESET}")
        sys.stdout.flush()
    
    def phase_complete(self, phase_num):
        """Mark phase complete"""
        self.clear_line()
        print(f"{C_BGREEN}[✓]{C_RESET} Phase {phase_num} complete\n")
        sys.stdout.flush()
    
    def phase_fail(self, phase_num, reason):
        """Mark phase failed"""
        self.clear_line()
        print(f"{C_BRED}[!]{C_RESET} Phase {phase_num} failed: {reason}\n")
        sys.stdout.flush()
    
    def status(self, message, icon="●"):
        """Display status message"""
        with self.lock:
            self.clear_line()
            print(f"{C_DIM}{self.get_spinner()} {C_RESET}{message}", end="")
            sys.stdout.flush()
    
    def success(self, message):
        """Display success message"""
        with self.lock:
            self.clear_line()
            print(f"{C_BGREEN}[✓]{C_RESET} {message}")
            sys.stdout.flush()
    
    def warning(self, message):
        """Display warning message"""
        with self.lock:
            self.clear_line()
            print(f"{C_BYELLOW}[!]{C_RESET} {message}")
            sys.stdout.flush()
    
    def error(self, message):
        """Display error message"""
        with self.lock:
            self.clear_line()
            print(f"{C_BRED}[✗]{C_RESET} {message}")
            sys.stdout.flush()
    
    def info(self, message):
        """Display info message"""
        with self.lock:
            self.clear_line()
            print(f"{C_CYAN}[i]{C_RESET} {message}")
            sys.stdout.flush()
    
    def section_header(self, title):
        """Display section header"""
        with self.lock:
            self.clear_line()
            print(f"\n{C_BOLD}{C_WHITE}▸ {title}{C_RESET}")
            sys.stdout.flush()
    
    def list_item(self, text, status=None):
        """Display list item with optional status"""
        with self.lock:
            if status == "ok":
                prefix = f"{C_BGREEN}✓{C_RESET}"
            elif status == "warn":
                prefix = f"{C_BYELLOW}⚠{C_RESET}"
            elif status == "fail":
                prefix = f"{C_BRED}✗{C_RESET}"
            else:
                prefix = f"{C_DIM}•{C_RESET}"
            
            print(f"  {prefix} {text}")
            sys.stdout.flush()
    
    def progress(self, current, total, label="Progress"):
        """Display progress bar"""
        with self.lock:
            self.clear_line()
            percent = (current / total) * 100 if total > 0 else 0
            bar_len = min(30, self.columns // 3)
            filled = int(bar_len * current / total) if total > 0 else 0
            bar = "█" * filled + "░" * (bar_len - filled)
            
            print(f"{label}: [{C_GREEN}{bar}{C_RESET}] {percent:.1f}% ({current}/{total})", end="")
            sys.stdout.flush()
    
    def summary(self, data):
        """Display operation summary"""
        self.clear_line()
        print(f"\n{C_BMAGENTA}{'═' * min(70, self.columns)}{C_RESET}")
        print(f"{C_BMAGENTA}OPERATION SUMMARY{C_RESET}")
        print(f"{C_BMAGENTA}{'═' * min(70, self.columns)}{C_RESET}\n")
        
        # Phase status
        print(f"{C_BOLD}Phase Status:{C_RESET}")
        for phase, status in data.get("phases", {}).items():
            if status.get("status") == "complete":
                print(f"  {C_BGREEN}[✓]{C_RESET} {phase}")
            elif status.get("status") == "running":
                print(f"  {C_BGREEN}[✓]{C_RESET} {phase}")
            elif status.get("status") == "failed":
                err = status.get("error", "unknown")
                print(f"  {C_BRED}[!]{C_RESET} {phase}: {err}")
            else:
                print(f"  {C_DIM}[?]{C_RESET} {phase}")
        
        # Targets
        targets = data.get("targets", {})
        print(f"\n{C_BOLD}Targets Found:{C_RESET} {len(targets)}")
        for mac, info in list(targets.items())[:5]:
            print(f"  {mac}: {info}")
        
        # Captured data
        captured = data.get("captured", {})
        print(f"\n{C_BOLD}Data Captured:{C_RESET}")
        print(f"  Credentials: {captured.get('credentials', 0)}")
        print(f"  Cards: {captured.get('cards', 0)}")
        print(f"  Tokens: {captured.get('tokens', 0)}")
        print(f"  Cryptograms: {captured.get('cryptograms', 0)}")
        
        # Runtime
        print(f"\n{C_BOLD}Runtime:{C_RESET} {data.get('runtime', 0)}s")
        
        print(f"\n{C_BMAGENTA}{'═' * min(70, self.columns)}{C_RESET}\n")
        sys.stdout.flush()
    
    def networks(self, networks, limit=15):
        """Display network list"""
        self.clear_line()
        print(f"\n{C_BCYAN}Found {len(networks)} networks:{C_RESET}")
        for net in networks[:limit]:
            ssid = net.get("ssid", "Unknown")
            print(f"  {C_WHITE}•{C_RESET} {ssid}")
        sys.stdout.flush()
    
    def targets_list(self, targets):
        """Display targets list"""
        self.clear_line()
        print(f"\n{C_BGREEN}Found {len(targets)} target(s):{C_RESET}")
        for mac, data in targets.items():
            probes = data.get("count", 0)
            signal = data.get("signal", 0)
            print(f"  {C_CYAN}{mac}{C_RESET}: {probes} probes, {signal}dBm")
        sys.stdout.flush()
    
    def risk_indicator(self, score):
        """Display risk level indicator"""
        if score >= 70:
            level = f"{C_BRED}CRITICAL{C_RESET}"
        elif score >= 40:
            level = f"{C_BYELLOW}HIGH{C_RESET}"
        elif score >= 20:
            level = f"{C_YELLOW}MEDIUM{C_RESET}"
        else:
            level = f"{C_GREEN}LOW{C_RESET}"
        
        self.clear_line()
        print(f"{C_DIM}Risk Level: {level} ({score}){C_RESET}")
        sys.stdout.flush()


class QuietModeUI:
    """Minimal output UI for quiet operation"""
    
    def __init__(self):
        self.phase = 0
        self.current_step = 0
    
    def header(self, title=None):
        print(f"\n{C_BOLD}WIFISINNER ULTIMATE{C_RESET}")
    
    def phase_start(self, phase_num, phase_name):
        self.phase = phase_num
        print(f"\n{C_BCYAN}[{phase_num}/{phase_name}]{C_RESET}")
    
    def step(self, step_num, message):
        self.current_step = step_num
        print(f"  {C_DIM}[{step_num}]{C_RESET} {message}")
    
    def success(self, message):
        print(f"  {C_BGREEN}✓{C_RESET} {message}")
    
    def warning(self, message):
        print(f"  {C_BYELLOW}⚠{C_RESET} {message}")
    
    def error(self, message):
        print(f"  {C_BRED}✗{C_RESET} {message}")
    
    def summary(self, data):
        print(f"\n{C_BOLD}Summary:{C_RESET}")
        print(f"  Phases: {len(data.get('phases', {}))}")
        print(f"  Targets: {len(data.get('targets', {}))}")
        print(f"  Runtime: {data.get('runtime', 0)}s")


def create_ui(mode="clean"):
    """Create appropriate UI based on mode"""
    if mode == "quiet":
        return QuietModeUI()
    else:
        return TerminalUI()
