#!/usr/bin/env python3
"""
Test log file generator.
Produces a realistic syslog-style file packed with IPv4 addresses (bare and CIDR)
and bundles it into a zip named to include a server hostname.

Usage:
    python3 generate_test_logs.py               # default 1MB
    python3 generate_test_logs.py -s 10MB
    python3 generate_test_logs.py -s 500KB
    python3 generate_test_logs.py -s 2GB
    python3 generate_test_logs.py -s 1MB --hostname myserver-prod-lon-02
    python3 generate_test_logs.py -s 1MB --out /tmp
"""

import argparse
import random
import re
import string
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Size parser
# ---------------------------------------------------------------------------

def parse_size(value: str) -> int:
    """Parse human size string to bytes. Accepts: 500KB, 10MB, 2GB, 1048576."""
    value = value.strip()
    m = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([KMGkmg][Bb]?)?", value)
    if not m:
        raise argparse.ArgumentTypeError(f"Unrecognised size: {value!r}. Use e.g. 1MB, 500KB, 2GB")
    num = float(m.group(1))
    unit = (m.group(2) or "").upper().rstrip("B")
    multipliers = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3}
    return int(num * multipliers[unit])

# ---------------------------------------------------------------------------
# Data pools
# ---------------------------------------------------------------------------

HOSTNAMES = [
    "web-prod-uk-01", "web-prod-uk-02", "api-prod-eu-01",
    "db-primary-lon", "db-replica-lon", "cache-prod-01",
    "lb-prod-uk-01",  "worker-prod-03", "monitor-prod-01",
]

SERVICES = [
    "sshd", "nginx", "kernel", "systemd", "cron",
    "postfix", "dockerd", "firewalld", "auditd", "sudo",
]

LOG_LEVELS = ["INFO", "WARN", "ERROR", "DEBUG", "NOTICE", "CRIT"]
LEVEL_WEIGHTS = [50, 20, 10, 15, 4, 1]

USERS = ["root", "deploy", "mickm", "ansible", "nagios", "www-data"]

ACTIONS = [
    "Accepted password for {user} from {ip} port {port}",
    "Failed password for {user} from {ip} port {port} ssh2",
    "Connection from {ip} port {port} on {lip} port 22",
    "Disconnected from {ip} port {port}",
    "New session {sid} of user {user}",
    "pam_unix(sshd:session): session opened for user {user}",
    "Received disconnect from {ip} port {port}: 11: disconnected by user",
    "Invalid user {user} from {ip} port {port}",
]

NGINX_TEMPLATES = [
    '{cip} - {user} [{ts}] "GET /api/v1/health HTTP/1.1" 200 512 "-" "curl/7.81.0"',
    '{cip} - - [{ts}] "POST /api/v1/data HTTP/1.1" 201 1024 "https://{rip}/" "Mozilla/5.0"',
    '{cip} - - [{ts}] "GET /static/app.js HTTP/1.1" 304 0 "-" "Mozilla/5.0"',
    '{cip} - {user} [{ts}] "DELETE /api/v1/session HTTP/1.1" 401 128 "-" "-"',
    '{cip} - - [{ts}] "GET / HTTP/1.1" 301 185 "-" "python-requests/2.28.0"',
]

FIREWALL_TEMPLATES = [
    "DROPPED IN=eth0 OUT= SRC={src} DST={dst} PROTO=TCP SPT={sp} DPT={dp} FLAGS=SYN",
    "ACCEPTED IN=eth0 OUT= SRC={src} DST={dst} PROTO=UDP SPT={sp} DPT=53",
    "FORWARD SRC={src} DST={dst} ROUTE via {gw} mask {mask}",
    "BLACKLIST match SRC={src} DST={dst} DPT={dp}",
    "NAT PREROUTING SRC={src} DST={dst} to {nat}",
]

NETWORK_TEMPLATES = [
    "route add -net {net}/{prefix} gw {gw}",
    "BGP UPDATE from {peer}: prefix {net}/{prefix} withdrawn",
    "OSPF: neighbor {peer} state -> FULL, area {net}/{prefix}",
    "SNMP trap from {src}: linkDown ifIndex=4",
    "VPN tunnel {src} <-> {dst} established, cipher AES-256",
    "DHCP OFFER to {src} lease {net}/{prefix} via {gw}",
]

# ---------------------------------------------------------------------------
# IP generators
# ---------------------------------------------------------------------------

def rand_ip(rng: random.Random) -> str:
    return ".".join(str(rng.randint(1, 254)) for _ in range(4))

def rand_private_ip(rng: random.Random) -> str:
    choice = rng.randint(0, 2)
    if choice == 0:
        return f"10.{rng.randint(0,255)}.{rng.randint(0,255)}.{rng.randint(1,254)}"
    elif choice == 1:
        return f"172.{rng.randint(16,31)}.{rng.randint(0,255)}.{rng.randint(1,254)}"
    else:
        return f"192.168.{rng.randint(0,255)}.{rng.randint(1,254)}"

def rand_cidr(rng: random.Random) -> str:
    base = rand_private_ip(rng)
    prefix = rng.choice([8, 16, 24, 25, 28, 30, 32])
    return f"{base}/{prefix}"

# ---------------------------------------------------------------------------
# Line generators
# ---------------------------------------------------------------------------

def make_timestamp(base: datetime, rng: random.Random) -> str:
    delta = timedelta(seconds=rng.randint(0, 86400))
    return (base + delta).strftime("%b %d %H:%M:%S")

def make_iso_timestamp(base: datetime, rng: random.Random) -> str:
    delta = timedelta(seconds=rng.randint(0, 86400))
    return (base + delta).strftime("%Y-%m-%dT%H:%M:%S.") + f"{rng.randint(0,999):03d}Z"

def syslog_line(rng: random.Random, base: datetime) -> str:
    ts      = make_timestamp(base, rng)
    host    = rng.choice(HOSTNAMES)
    svc     = rng.choice(SERVICES)
    pid     = rng.randint(1000, 65535)
    tmpl    = rng.choice(ACTIONS)
    ip      = rand_private_ip(rng)
    lip     = rand_private_ip(rng)
    port    = rng.randint(1024, 65535)
    user    = rng.choice(USERS)
    sid     = rng.randint(1, 999)
    msg     = tmpl.format(ip=ip, lip=lip, port=port, user=user, sid=sid)
    level   = rng.choices(LOG_LEVELS, weights=LEVEL_WEIGHTS)[0]
    return f"{ts} {host} {svc}[{pid}]: [{level}] {msg}\n"

def nginx_line(rng: random.Random, base: datetime) -> str:
    tmpl = rng.choice(NGINX_TEMPLATES)
    ts   = make_timestamp(base, rng)
    cip  = rand_ip(rng)
    rip  = rand_ip(rng)
    user = rng.choice(USERS + ["-"])
    return tmpl.format(cip=cip, rip=rip, ts=ts, user=user) + "\n"

def firewall_line(rng: random.Random, base: datetime) -> str:
    ts   = make_iso_timestamp(base, rng)
    tmpl = rng.choice(FIREWALL_TEMPLATES)
    src  = rand_ip(rng)
    dst  = rand_private_ip(rng)
    gw   = rand_private_ip(rng)
    nat  = rand_private_ip(rng)
    mask = rng.choice(["255.255.255.0", "255.255.0.0", "255.0.0.0"])
    sp   = rng.randint(1024, 65535)
    dp   = rng.choice([22, 80, 443, 3306, 5432, 6379, 8080])
    return f"{ts} FIREWALL: " + tmpl.format(
        src=src, dst=dst, gw=gw, nat=nat, mask=mask, sp=sp, dp=dp
    ) + "\n"

def network_line(rng: random.Random, base: datetime) -> str:
    ts   = make_iso_timestamp(base, rng)
    tmpl = rng.choice(NETWORK_TEMPLATES)
    src  = rand_ip(rng)
    dst  = rand_ip(rng)
    gw   = rand_private_ip(rng)
    net  = rand_private_ip(rng).rsplit(".", 1)[0] + ".0"
    peer = rand_ip(rng)
    prefix = rng.choice([8, 16, 24, 30])
    return f"{ts} NETWORK: " + tmpl.format(
        src=src, dst=dst, gw=gw, net=net, peer=peer, prefix=prefix
    ) + "\n"

LINE_GENERATORS = [
    (syslog_line,   50),
    (nginx_line,    25),
    (firewall_line, 15),
    (network_line,  10),
]
GEN_FUNCS, GEN_WEIGHTS = zip(*LINE_GENERATORS)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate(target_bytes: int, rng: random.Random) -> bytes:
    base = datetime(2026, 6, 1)
    buf  = []
    total = 0
    while total < target_bytes:
        fn   = rng.choices(GEN_FUNCS, weights=GEN_WEIGHTS)[0]
        line = fn(rng, base)
        buf.append(line)
        total += len(line)
    return "".join(buf).encode("utf-8")[:target_bytes]


def main():
    parser = argparse.ArgumentParser(
        description="Generate a synthetic log zip for obfuscation testing."
    )
    parser.add_argument(
        "-s", "--size",
        default="1MB",
        type=parse_size,
        metavar="SIZE",
        help="Target uncompressed log size (e.g. 500KB, 1MB, 10MB, 2GB). Default: 1MB",
    )
    parser.add_argument(
        "--hostname",
        default="server-prod-uk-01",
        metavar="HOSTNAME",
        help="Hostname embedded in the zip filename. Default: server-prod-uk-01",
    )
    parser.add_argument(
        "--seed",
        default=42,
        type=int,
        metavar="SEED",
        help="RNG seed for reproducible output. Default: 42",
    )
    parser.add_argument(
        "--out",
        default=".",
        metavar="DIR",
        help="Output directory. Default: current directory",
    )
    args = parser.parse_args()

    out_dir  = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_name = out_dir / f"test_logs_{args.hostname}.zip"
    log_name = f"test_logs_{args.hostname}.log"

    rng = random.Random(args.seed)

    size_label = args.size
    for unit, div in [("GB", 1024**3), ("MB", 1024**2), ("KB", 1024)]:
        if args.size >= div:
            size_label = f"{args.size/div:.1f}{unit}"
            break

    print(f"Generating {size_label} of log data (seed={args.seed})...")
    data = generate(args.size, rng)

    print(f"Writing {zip_name.name}...")
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr(log_name, data)

    ratio = len(data) / zip_name.stat().st_size
    print(f"Done.")
    print(f"  Log size (uncompressed) : {len(data):,} bytes ({size_label})")
    print(f"  Zip size (compressed)   : {zip_name.stat().st_size:,} bytes")
    print(f"  Compression ratio       : {ratio:.1f}x")
    print(f"  Output                  : {zip_name}")


if __name__ == "__main__":
    main()
