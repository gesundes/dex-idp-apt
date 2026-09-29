#!/usr/bin/env bash
set -euo pipefail
tag="$1"
arch="$2"
version="${tag#v}"
if [[ ! "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then echo "Invalid tag: $tag" >&2; exit 1; fi
case "$arch" in amd64|arm64) ;; *) echo "Unsupported architecture: $arch" >&2; exit 1 ;; esac
git -C dex-src fetch --depth=1 origin "refs/tags/$tag"
git -C dex-src checkout --detach FETCH_HEAD
rm -rf package
mkdir -p "package/DEBIAN" "package/usr/bin" "package/usr/share/doc/dex"
(cd dex-src && CGO_ENABLED=1 go build -trimpath -ldflags "-s -w -X main.version=$tag" -o ../package/usr/bin/dex ./cmd/dex)
cp dex-src/LICENSE package/usr/share/doc/dex/copyright
cat > package/DEBIAN/control <<EOF
Package: dex
Version: $version
Section: net
Priority: optional
Architecture: $arch
Maintainer: Dex APT Repository <noreply@github.com>
Homepage: https://github.com/dexidp/dex
Depends: libc6
Description: Dex OpenID Connect identity provider
 Unofficial package built from the upstream Dex release tag.
EOF
dpkg-deb --build --root-owner-group package "dex_${version}_${arch}.deb"
dpkg-deb --field "dex_${version}_${arch}.deb" Package Version Architecture
