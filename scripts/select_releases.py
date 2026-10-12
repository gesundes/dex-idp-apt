#!/usr/bin/env python3
"""Choose published Dex tags newer than the newest packaged version."""
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

VERSION = re.compile(r"v(\d+)\.(\d+)\.(\d+)$")


def version(tag):
    match = VERSION.fullmatch(tag)
    return tuple(map(int, match.groups())) if match else None


def select(releases, existing, architectures=None):
    if architectures is None:
        architectures = {}
    stable = [(version(item["tag_name"]), item["tag_name"]) for item in releases
              if not item["draft"] and not item["prerelease"] and version(item["tag_name"])]
    stable.sort(reverse=True)
    if not stable:
        raise ValueError("No stable Dex releases found")
    if not existing:
        return [stable[0][1]]
    newest = max(existing)
    tags = [tag for number, tag in reversed(stable) if number > newest]
    if architectures.get(newest) != {"amd64", "arm64"}:
        for number, tag in stable:
            if number == newest:
                tags.insert(0, tag)
                break
    return tags


def main():
    architectures = {}
    for path in Path("apt-repo/pool/main").glob("dexidp_*_*.deb"):
        match = re.fullmatch(r"dexidp_(\d+)\.(\d+)\.(\d+)_(amd64|arm64)\.deb", path.name)
        if match:
            architectures.setdefault(tuple(map(int, match.groups()[:3])), set()).add(match.group(4))
    existing = set(architectures)
    rebuild = os.environ.get("REBUILD", "false") == "true"
    requested = os.environ.get("REBUILD_TAG", "")
    if rebuild and not version(requested):
        raise ValueError("Full rebuild requires a stable vX.Y.Z tag")
    token = os.environ.get("GH_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "dex-idp-apt"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    releases = []
    for page in range(1, 11):
        request = Request(f"https://api.github.com/repos/dexidp/dex/releases?per_page=100&page={page}", headers=headers)
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        releases.extend(batch)
        if not batch or (rebuild and any(item["tag_name"] == requested for item in batch)) or (not rebuild and (not existing or any(version(item["tag_name"]) in existing for item in batch))):
            break
    if rebuild:
        if not any(item["tag_name"] == requested and not item["draft"] and not item["prerelease"] for item in releases):
            raise ValueError("Requested stable release not found")
        tags = [requested]
    else:
        tags = select(releases, existing, architectures)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"tags={json.dumps(tags, separators=(',', ':'))}\n")
        output.write(f"has_new={'true' if tags else 'false'}\n")
    print(f"Dex releases to package: {tags}")


if __name__ == "__main__":
    main()
