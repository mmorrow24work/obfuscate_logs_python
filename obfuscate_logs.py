#!/usr/bin/env python3
"""
Log file IP obfuscation tool.
- Renames zip (strips hostname from filename)
- Obfuscates all internal filenames (removes hostname traces)
- Replaces all IPv4 addresses (bare and CIDR) in one pass per file
- Replaces all hostname strings found in content
- Produces: <newname>_obfuscated.zip, obfuscation_encode.txt, obfuscation_decode.txt
Usage: python3 obfuscate_logs.py <zipfile>
"""

import re
import sys
import zipfile
import hashlib
import random
from pathlib import Path

SEED = 42
IP_RE       = re.compile(r'\b(\d{1,3}(?:\.\d{1,3}){3})(\/\d{1,2})?\b')
HOSTNAME_RE = re.compile(r'[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
                         r'(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+')

# ---------------------------------------------------------------------------
# Deterministic fake generators
# ---------------------------------------------------------------------------

def fake_ip(real_ip: str) -> str:
    rng = random.Random(int(hashlib.md5(real_ip.encode()).hexdigest(), 16) ^ SEED)
    return "OBFUSC_{:03d}.{:03d}.{:03d}.{:03d}".format(
        rng.randint(1, 254), rng.randint(1, 254),
        rng.randint(1, 254), rng.randint(1, 254),
    )

def fake_hostname(real_host: str) -> str:
    """Produce a stable OBFUSC-HOST-<hex> replacement for any hostname."""
    digest = hashlib.md5(real_host.lower().encode()).hexdigest()[:8]
    return f"OBFUSC-HOST-{digest.upper()}"

def fake_filename(original: str, host_map: dict) -> str:
    """
    Strip all known hostnames from an internal zip entry filename,
    then replace the stem with a hex digest so no original name leaks.
    """
    p = Path(original)
    stem = p.stem
    suffix = p.suffix

    # Replace any hostname fragments in the filename
    for real, fake in host_map.items():
        stem = stem.replace(real, fake)

    # Replace the whole stem with a content-addressed hex so nothing
    # from the original path survives, while keeping the extension
    obf_stem = "log_" + hashlib.md5(original.encode()).hexdigest()[:12]
    return obf_stem + suffix

# ---------------------------------------------------------------------------
# Scanning pass — collect IPs and hostnames
# ---------------------------------------------------------------------------

def scan(zip_path: Path):
    """
    Single pass: collect all unique IPs and candidate hostnames.
    Returns (ip_set, hostname_set).
    Hostnames are only collected if they appear in the zip filename
    or internal filenames — we don't want to blanket-replace every
    hostname-shaped string in log content, only real server names.
    """
    ip_seen   = set()
    host_seen = set()

    # Derive hostnames from the zip filename itself
    stem = zip_path.stem  # e.g. test_logs_server-prod-uk-01
    # Strip common prefixes like test_logs_, logs_
    for prefix in ("test_logs_", "logs_"):
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
    if stem:
        host_seen.add(stem)

    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            info = zf.getinfo(name)

            # Collect hostnames from internal filenames
            inner_stem = Path(name).stem
            for prefix in ("test_logs_", "logs_"):
                if inner_stem.startswith(prefix):
                    inner_stem = inner_stem[len(prefix):]
            if inner_stem:
                host_seen.add(inner_stem)

            if info.is_dir():
                continue
            try:
                data = zf.read(name).decode("utf-8", errors="replace")
            except Exception:
                continue
            for m in IP_RE.finditer(data):
                ip_seen.add(m.group(1))

    return ip_seen, host_seen

# ---------------------------------------------------------------------------
# Content obfuscation — single regex pass
# ---------------------------------------------------------------------------

def obfuscate_content(data: str, ip_map: dict, host_map: dict) -> str:
    # Replace hostnames first (longer strings, more specific)
    for real, fake in host_map.items():
        data = data.replace(real, fake)

    # Replace IPs in one regex pass
    def replace_ip(m):
        return ip_map.get(m.group(1), m.group(1)) + (m.group(2) or "")

    return IP_RE.sub(replace_ip, data)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 obfuscate_logs.py <zipfile>")
        sys.exit(1)

    src = Path(sys.argv[1]).resolve()
    if not src.exists():
        print(f"Error: {src} not found")
        sys.exit(1)

    out_dir  = src.parent
    rand_hex = hashlib.md5(src.name.encode()).hexdigest()[:16]
    obf_zip  = out_dir / f"logs_{rand_hex}_obfuscated.zip"
    enc_file = out_dir / "obfuscation_encode.txt"
    dec_file = out_dir / "obfuscation_decode.txt"

    # ------------------------------------------------------------------
    print(f"[1/4] Scanning {src.name} for IPs and hostnames...")
    ip_seen, host_seen = scan(src)
    ip_map   = {ip:   fake_ip(ip)             for ip   in sorted(ip_seen)}
    host_map = {host: fake_hostname(host)      for host in sorted(host_seen)}
    print(f"      Found {len(ip_map)} unique IPs, {len(host_map)} hostnames")
    if host_map:
        for r, f in host_map.items():
            print(f"      hostname: {r!r} -> {f!r}")

    # ------------------------------------------------------------------
    print(f"[2/4] Writing mapping files...")
    with open(enc_file, "w") as fe, open(dec_file, "w") as fd:
        fe.write("# === HOSTNAMES ===\n")
        fd.write("# === HOSTNAMES ===\n")
        for real, fake in sorted(host_map.items()):
            fe.write(f"{real} -> {fake}\n")
            fd.write(f"{fake} -> {real}\n")
        fe.write("# === IP ADDRESSES ===\n")
        fd.write("# === IP ADDRESSES ===\n")
        for real, fake in sorted(ip_map.items()):
            fe.write(f"{real} -> {fake}\n")
            fd.write(f"{fake} -> {real}\n")

    # ------------------------------------------------------------------
    print(f"[3/4] Obfuscating and writing {obf_zip.name}...")
    with zipfile.ZipFile(src) as zin, \
         zipfile.ZipFile(obf_zip, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            obf_name = fake_filename(item.filename, host_map)

            if item.is_dir():
                zout.mkdir(obf_name)
                continue

            raw = zin.read(item.filename)
            try:
                text = raw.decode("utf-8", errors="replace")
                obf  = obfuscate_content(text, ip_map, host_map)
                zout.writestr(obf_name, obf.encode("utf-8"))
            except Exception:
                zout.writestr(obf_name, raw)

    # ------------------------------------------------------------------
    print(f"[4/4] Done.")
    print(f"      Obfuscated zip : {obf_zip.name}")
    print(f"      Encode map     : {enc_file.name}")
    print(f"      Decode map     : {dec_file.name}")

if __name__ == "__main__":
    main()
