# Dex APT Repository

Unofficial APT repository for [Dex](https://github.com/dexidp/dex). GitHub Actions builds packages from published stable Dex release tags for native `amd64` and `arm64` GitHub hosted Linux runners. Packages are retained in `apt-repo/pool/main`, indexed for APT, signed, and published on GitHub Pages.

The daily workflow checks the Dex releases API at 06:00 UTC. On the first run it builds the latest stable release. Later runs add every newer stable release, retaining earlier package versions. Changing `packaging/revision` causes the newest existing Dex version to be rebuilt with the new package layout. A manual run is available in GitHub Actions. Failed builds stop publication, so one architecture cannot silently disappear from the repository.

## Setup

1. Ensure GnuPG (`gpg`) is available in `PATH`, then run `bash scripts/generate-gpg-key.sh` to create a repository signing key. The script works with the Bash 3.2 shipped with macOS. Add the armored private key, passphrase, and printed key ID as repository Actions secrets named `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE`, and `GPG_KEY_ID`. Keep `dex-apt-private.key` private.
2. In repository Settings → Pages, select **GitHub Actions** as the source.
3. Run **Update APT Repository** manually once. Subsequent runs are scheduled daily.

The repository URL is `https://gesundes.github.io/dex-idp-apt`. Once the first run has succeeded, add its key and source:

```bash
curl -fsSL https://gesundes.github.io/dex-idp-apt/pubkey.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/dex.gpg
```

```bash
echo 'deb [signed-by=/etc/apt/keyrings/dex.gpg] https://gesundes.github.io/dex-idp-apt stable main' | sudo tee /etc/apt/sources.list.d/dex.list
```

```bash
sudo apt update
```

The package name is `dex`. It contains `/usr/bin/dex`, `/lib/systemd/system/dexidp.service`, and `/etc/dex/config.yaml`. On first installation, the package creates a `dexidp` system user, enables `dexidp.service`, and starts it when systemd is running. The configuration file is a dpkg conffile, so local edits are retained on upgrades. The unit runs as `dexidp`, stores SQLite data in `/var/lib/dex`, and listens only on `127.0.0.1:5556` by default. The starter configuration enables the local password connector but creates no users or clients.

Before connecting applications to Dex, edit `/etc/dex/config.yaml` to set the real issuer URL, configure TLS or a trusted reverse proxy, and add connectors and clients. Then restart the service:

```bash
sudo systemctl restart dexidp.service
```

Check whether it is enabled and running:

```bash
systemctl status dexidp.service
```

The service definition is maintained in [`packaging/dexidp.service`](packaging/dexidp.service), and the starter configuration is in [`packaging/config.yaml`](packaging/config.yaml).

## Layout

- `apt-repo/pool/main/`: retained `.deb` versions.
- `apt-repo/dists/stable/main/binary-{amd64,arm64}/`: APT package indexes.
- `apt-repo/dists/stable/Release`, `InRelease`, `Release.gpg`: signed repository metadata.
- `apt-repo/pubkey.gpg`: public signing key for clients.

Packages are built from upstream source tags because current Dex releases have no binary assets. Builds use native GitHub hosted runners with CGO enabled for Dex's SQLite support. The `ubuntu-24.04-arm` runner is available for public repositories; if runner availability changes, that architecture must be disabled deliberately rather than publishing a partial repository.

This is an unofficial repository. Dex upstream maintains the [source releases](https://github.com/dexidp/dex/releases).
