#!/usr/bin/env python3
"""
Log file IP obfuscation tool.
- Renames zip (strips hostname from filename)
- Replaces all IPv4 addresses (bare and CIDR) in one pass per file
- Produces: <newname>_obfuscated.zip, obfuscation_encode.txt, obfuscation_decode.txt
Usage: python3 obfuscate_logs.py <zipfile>
"""

import re
import sys
import os
import zipfile
import random
import hashlib
from pathlib import Path

SEED = 42
IP_RE = re.compile(r'\b(\d{1,3}(?:\.\d{1,3}){3})(\/\d{1,2})?\b')

def fake_ip(real_ip: str, rng: random.Random) -> str:
    """Generate a deterministic fake IP using a seeded RNG keyed on the real IP."""
    # Per-IP seed so same IP always gets same fake regardless of discovery order
    ip_rng = random.Random(int(hashlib.md5(real_ip.encode()).hexdigest(), 16) ^ SEED)
    return "OBFUSC_{:03d}.{:03d}.{:03d}.{:03d}".format(
        ip_rng.randint(1, 254), ip_rng.randint(1, 254),
        ip_rng.randint(1, 254), ip_rng.randint(1, 254)
    )

def build_ip_map(zip_path: Path) -> dict:
    """Single pass through all files to collect unique IPs."""
    seen = set()
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            info = zf.getinfo(name)
            if info.is_dir():
                continue
            try:
                data = zf.read(name).decode("utf-8", errors="replace")
            except Exception:
                continue
            for m in IP_RE.finditer(data):
                seen.add(m.group(1))
    rng = random.Random(SEED)
    return {ip: fake_ip(ip, rng) for ip in sorted(seen)}

def obfuscate_content(data: str, ip_map: dict, pattern: re.Pattern) -> str:
    """Single-pass replacement using regex sub with a lookup callback."""
    def replace(m):
        real_ip = m.group(1)
        cidr = m.group(2) or ""
        return ip_map.get(real_ip, real_ip) + cidr
    return pattern.sub(replace, data)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 obfuscate_logs.py <zipfile>")
        sys.exit(1)

    src = Path(sys.argv[1]).resolve()
    if not src.exists():
        print(f"Error: {src} not found")
        sys.exit(1)

    out_dir = src.parent
    rand_hex = hashlib.md5(src.name.encode()).hexdigest()[:16]
    new_stem = f"logs_{rand_hex}"
    obf_zip  = out_dir / f"{new_stem}_obfuscated.zip"
    enc_file = out_dir / "obfuscation_encode.txt"
    dec_file = out_dir / "obfuscation_decode.txt"

    print(f"[1/4] Scanning for IPs in {src.name}...")
    ip_map = build_ip_map(src)
    print(f"      Found {len(ip_map)} unique IPs")

    print(f"[2/4] Writing mapping files...")
    with open(enc_file, "w") as fe, open(dec_file, "w") as fd:
        for real, fake in sorted(ip_map.items()):
            fe.write(f"{real} -> {fake}\n")
            fd.write(f"{fake} -> {real}\n")

    print(f"[3/4] Obfuscating and writing {obf_zip.name}...")
    with zipfile.ZipFile(src) as zin, \
         zipfile.ZipFile(obf_zip, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.is_dir():
                zout.mkdir(item)
                continue
            raw = zin.read(item.filename)
            try:
                text = raw.decode("utf-8", errors="replace")
                obf  = obfuscate_content(text, ip_map, IP_RE)
                zout.writestr(item, obf.encode("utf-8"))
            except Exception:
                # Binary file — copy as-is
                zout.writestr(item, raw)

    print(f"[4/4] Done.")
    print(f"      Obfuscated zip : {obf_zip.name}")
    print(f"      Encode map     : {enc_file.name}")
    print(f"      Decode map     : {dec_file.name}")

if __name__ == "__main__":
    main()
