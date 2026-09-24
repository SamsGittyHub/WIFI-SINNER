# wifisint — Evil Twin WiFi Honeypot

A terminal-based evil-twin attack tool. It broadcasts a fake open hotspot called
**FREE WIFI**, auto-pops a phishing sign-in portal on victim devices, and harvests
everything it can while they're connected.

## What it steals

| Vector | Method |
|---|---|
| Account credentials | Fake captive portal (Email / Google / Facebook / Instagram tabs) — auto-pops on iOS, Android, Windows, macOS |
| DNS surveillance | All queries logged (every site visited), hijacked to the portal until the victim signs in |
| TLS hostnames | SNI extraction from ClientHello (visited HTTPS sites, post-login) |
| Plaintext HTTP | Basic-Auth headers, cookies/session tokens, POST bodies, tokens in URLs |
| Device fingerprints | MAC, DHCP hostname, OS, user-agent, IP |
| Full traffic | Complete `.pcap` of everything victims send/receive |
| Internet sharing | NAT through your wired uplink so victims stay online (and keep leaking) |

## Install

```bash
sudo apt install dnsmasq-base tcpdump iw    # iw optional (deauth only)
python3 -m pip install --break-system-packages scapy
```

## Run

```bash
sudo python3 wifisint.py                          # "FREE WIFI" on channel 6
sudo python3 wifisint.py --ssid "Airport_Free"    # custom SSID
sudo python3 wifisint.py --deauth "HomeNet"       # kick clients off a real network
sudo python3 wifisint.py --scan                   # list nearby networks
sudo python3 wifisint.py --selftest               # offline parser tests
```

Options: `--iface`, `--channel`, `--password` (WPA2), `--gateway`, `--no-nat`.

## How it works

1. Creates an open AP via NetworkManager (`wlp8s0`, AP mode). NM puts it in
   `shared` mode, so NM runs its own dnsmasq (DHCP on `10.0.0.10`–`10.0.0.254`)
   and NATs traffic out your wired uplink.
2. `iptables` DNAT redirects every victim's port-53 traffic to the built-in
   DNS server on `10.0.0.1:5353`, which hijacks **all** domains to the honeypot
   until the victim authenticates (then forwards to real resolvers).
3. Victim's OS detects the captive portal (hotspot-detect / generate_204 /
   connecttest endpoints) and pops the fake sign-in page automatically.
4. On submit, credentials are saved and the victim is whitelisted — they get
   real internet through NAT while every packet is sniffed and recorded.
5. `--deauth` additionally hammers a chosen real network with deauth frames
   (via a monitor-mode `mon0`) so its clients drop and find FREE WIFI.

> Note: NetworkManager 1.46 forces AP connections to `ipv4.method=shared`, so
> the tool embraces that and hijacks DNS with DNAT instead of running its own
> DHCP/DNS stack.

## Loot

Every run writes to `loot/<timestamp>/`:

- `credentials.json` — phished logins
- `http_secrets.json` — Basic-Auth, cookies, POST bodies
- `dns_queries.json`, `tls_hosts.json`, `clients.json`
- `full_capture.pcap`, `dhcp.log`, `session_summary.txt`

Ctrl+C tears everything down cleanly and prints the stolen-credential summary.

## Notes

- Use only on networks/devices you own or are authorized to test.
- HTTPS bodies can't be decrypted without a trusted CA, hence portal phishing
  for credentials + passive capture for everything else.
- The WiFi adapter must support AP mode (`nmcli device show` → WIFI-PROPERTIES.AP).
# WIFI-SINNER
