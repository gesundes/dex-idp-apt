#!/usr/bin/env python3
"""Generate reproducible APT indices for both architectures."""
from datetime import datetime, timezone
import gzip
from hashlib import md5, sha256, sha512
from html import escape
import os
from pathlib import Path
import subprocess

ROOT = Path("apt-repo")
DIST = ROOT / "dists/stable"
POOL = ROOT / "pool/main"


def package_field(path, name):
    return subprocess.check_output(["dpkg-deb", "--field", str(path), name], text=True).strip()


def main():
    packages = sorted(POOL.glob("*.deb"))
    for arch in ("amd64", "arm64"):
        directory = DIST / "main" / f"binary-{arch}"
        directory.mkdir(parents=True, exist_ok=True)
        entries = []
        for package in packages:
            if package_field(package, "Architecture") != arch:
                continue
            control = subprocess.check_output(["dpkg-deb", "--field", str(package)], text=True).rstrip()
            data = package.read_bytes()
            entries.append(f"{control}\nFilename: pool/main/{package.name}\nSize: {len(data)}\nMD5sum: {md5(data).hexdigest()}\nSHA256: {sha256(data).hexdigest()}\nSHA512: {sha512(data).hexdigest()}\n")
        content = ("\n".join(entries) + "\n" if entries else "").encode()
        (directory / "Packages").write_bytes(content)
        (directory / "Packages.gz").write_bytes(gzip.compress(content, compresslevel=9, mtime=0))
    files = sorted(path for path in DIST.rglob("*") if path.name in ("Packages", "Packages.gz"))
    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    lines = ["Origin: Dex APT Repository", "Label: dex-idp-apt", "Suite: stable", "Codename: stable", "Architectures: amd64 arm64", "Components: main", "Description: Unofficial Dex packages built from upstream releases", f"Date: {date}"]
    for name, digest in (("MD5Sum", md5), ("SHA256", sha256), ("SHA512", sha512)):
        lines.append(f"{name}:")
        for path in files:
            data = path.read_bytes()
            lines.append(f" {digest(data).hexdigest()} {len(data):16d} {path.relative_to(DIST)}")
    (DIST / "Release").write_text("\n".join(lines) + "\n")
    owner = os.environ.get("GITHUB_REPOSITORY", "gesundes/dex-idp-apt")
    owner_name, repo = owner.split("/", 1)
    url = f"https://{owner_name}.github.io/{repo}"
    links = "\n".join(f'<li><a href="pool/main/{escape(path.name)}">{escape(path.name)}</a></li>' for path in packages)
    (ROOT / "index.html").write_text(f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Dex APT Repository</title>
<h1>Dex APT Repository</h1><p>Unofficial packages built from <a href="https://github.com/dexidp/dex/releases">Dex releases</a>.</p>
<p>Architectures: amd64, arm64. Distribution: stable. Component: main.</p>
<pre>curl -fsSL {url}/pubkey.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/dex.gpg
echo "deb [signed-by=/etc/apt/keyrings/dex.gpg] {url} stable main" | sudo tee /etc/apt/sources.list.d/dex.list
sudo apt update
sudo apt install dexidp</pre>
<h2>Packages</h2><ul>{links}</ul><p><a href="pubkey.gpg">Repository signing key</a></p></html>
''')


if __name__ == "__main__":
    main()
