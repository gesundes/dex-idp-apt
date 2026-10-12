#!/usr/bin/env python3
"""Verify generated index payloads and links before committing."""
import gzip
from hashlib import sha256
import os
from pathlib import Path

root = Path('apt-repo')
indexed = set()
for arch in ('amd64', 'arm64'):
    index = root / f'dists/stable/main/binary-{arch}/Packages'
    assert gzip.decompress(index.with_suffix('.gz').read_bytes()) == index.read_bytes()
    for entry in index.read_text().strip().split('\n\n'):
        fields = dict(line.split(': ', 1) for line in entry.splitlines() if ': ' in line and not line.startswith(' '))
        assert fields['Package'] == 'dexidp'
        assert fields['Architecture'] == arch
        assert '-' not in fields['Version']
        path = root / fields['Filename']
        assert path.name == f"dexidp_{fields['Version']}_{arch}.deb"
        assert len(path.read_bytes()) == int(fields['Size'])
        assert sha256(path.read_bytes()).hexdigest() == fields['SHA256']
        assert fields['Filename'] in (root / 'index.html').read_text()
        indexed.add(path)
assert indexed == set((root / 'pool/main').glob('*.deb'))
assert 'sudo apt install dexidp' in (root / 'index.html').read_text()
if os.environ.get('REBUILD') == 'true':
    tag = os.environ['REBUILD_TAG'].removeprefix('v')
    assert {p.name for p in indexed} == {f'dexidp_{tag}_{arch}.deb' for arch in ('amd64', 'arm64')}
