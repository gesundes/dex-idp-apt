#!/usr/bin/env bash
set -euo pipefail

if ! command -v gpg >/dev/null 2>&1; then
    printf 'GnuPG (gpg) is required. Make it available in PATH, then run this script again.\n' >&2
    exit 1
fi

umask 077
read -r -p 'Signing name: ' name
read -r -p 'Signing email: ' email
read -r -s -p 'Key passphrase: ' passphrase
printf '\n'

if [[ -z "$name" || -z "$email" || -z "$passphrase" ]]; then
    printf 'Name, email, and key passphrase must all be non-empty.\n' >&2
    exit 1
fi

uid="$name <$email>"
if [[ -e dex-apt-private.key || -e dex-apt-public.key ]]; then
    printf 'Key output files already exist in the current directory. Move them before creating a new key.\n' >&2
    exit 1
fi

existing_key="$(gpg --with-colons --list-secret-keys "$uid" 2>/dev/null | awk -F: '$1 == "sec" { print $5; exit }' || true)"
if [[ -n "$existing_key" ]]; then
    printf 'A secret key already exists for %s. Use a different signing identity.\n' "$uid" >&2
    exit 1
fi

gpg --batch --pinentry-mode loopback --passphrase-fd 3 --quick-generate-key "$uid" rsa4096 sign 2y 3<<< "$passphrase"
key_id="$(gpg --with-colons --list-secret-keys "$uid" | awk -F: '$1 == "fpr" { print $10; exit }')"
if [[ -z "$key_id" ]]; then
    printf 'Could not find the newly generated key fingerprint.\n' >&2
    exit 1
fi

gpg --batch --pinentry-mode loopback --passphrase-fd 3 --armor --export-secret-keys "$key_id" > dex-apt-private.key 3<<< "$passphrase"
gpg --armor --export "$key_id" > dex-apt-public.key
chmod 600 dex-apt-private.key
unset passphrase
printf 'GPG_KEY_ID=%s\nGPG_PRIVATE_KEY is in dex-apt-private.key\nPublic key is in dex-apt-public.key\n' "$key_id"
