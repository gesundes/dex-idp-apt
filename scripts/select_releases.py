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


def select(releases, existing):
    stable = [(version(item["tag_name"]), item["tag_name"]) for item in releases
              if not item["draft"] and not item["prerelease"] and version(item["tag_name"])]
    stable.sort(reverse=True)
    if not stable:
        raise ValueError("No stable Dex releases found")
    if not existing:
        return [stable[0][1]]
    newest = max(existing)
    return [tag for number, tag in reversed(stable) if number > newest]


def main():
    existing = {tuple(map(int, match.groups()))
                for path in Path("apt-repo/pool/main").glob("dex_*_*.deb")
                if (match := re.fullmatch(r"dex_(\d+)\.(\d+)\.(\d+)_.*\.deb", path.name))}
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
        if not batch or not existing or any(version(item["tag_name"]) in existing for item in batch):
            break
    tags = select(releases, existing)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"tags={json.dumps(tags, separators=(',', ':'))}\n")
        output.write(f"has_new={'true' if tags else 'false'}\n")
    print(f"Dex releases to package: {tags}")


if __name__ == "__main__":
    main()
