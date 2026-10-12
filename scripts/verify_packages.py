#!/usr/bin/env python3
"""Exercise native packages on a disposable Linux systemd runner."""
from pathlib import Path
import subprocess
import sys


def run(*args):
    return subprocess.check_output(args, text=True).strip()


for package in sorted(Path(sys.argv[1]).glob('*.deb')):
    name, version, arch = package.stem.split('_')
    assert name == 'dexidp' and '-' not in version
    for field, expected in [('Package', name), ('Version', version), ('Architecture', arch)]:
        assert run('dpkg-deb', '--field', str(package), field) == expected
    contents = run('dpkg-deb', '--contents', str(package))
    for path in ['usr/bin/dex', 'etc/dex/config.yaml', 'lib/systemd/system/dexidp.service', 'usr/share/doc/dexidp/copyright']:
        assert path in contents, path
    run('sudo', 'dpkg', '-i', str(package))
    assert run('systemctl', 'is-enabled', 'dexidp.service') == 'enabled'
    assert run('systemctl', 'is-active', 'dexidp.service') == 'active'
    run('sudo', 'sh', '-c', 'echo "# package verification" >> /etc/dex/config.yaml')
    run('sudo', 'dpkg', '-i', str(package))
    assert '# package verification' in run('sudo', 'cat', '/etc/dex/config.yaml')
    run('sudo', 'dpkg', '--remove', 'dexidp')
    assert subprocess.run(['systemctl', 'is-active', '--quiet', 'dexidp.service']).returncode != 0
    run('sudo', 'dpkg', '--purge', 'dexidp')
