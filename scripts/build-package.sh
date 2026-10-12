#!/usr/bin/env bash
set -euo pipefail
tag="$1"
arch="$2"
version="${tag#v}"
package_version="${version}"
if [[ ! "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then echo "Invalid tag: $tag" >&2; exit 1; fi
case "$arch" in amd64|arm64) ;; *) echo "Unsupported architecture: $arch" >&2; exit 1 ;; esac
git -C dex-src fetch --depth=1 origin "refs/tags/$tag"
git -C dex-src checkout --detach FETCH_HEAD
rm -rf package
mkdir -p "package/DEBIAN" "package/usr/bin" "package/usr/share/doc/dexidp" "package/etc/dex" "package/lib/systemd/system"
(cd dex-src && CGO_ENABLED=1 go build -trimpath -ldflags "-s -w -X main.version=$tag" -o ../package/usr/bin/dex ./cmd/dex)
cp dex-src/LICENSE package/usr/share/doc/dexidp/copyright
cp packaging/config.yaml package/etc/dex/config.yaml
cp packaging/dexidp.service package/lib/systemd/system/dexidp.service
cp packaging/postinst packaging/prerm packaging/postrm package/DEBIAN/
chmod 0755 package/DEBIAN/postinst package/DEBIAN/prerm package/DEBIAN/postrm
printf '/etc/dex/config.yaml\n' > package/DEBIAN/conffiles
cat > package/DEBIAN/control <<EOF
Package: dexidp
Version: $package_version
Section: net
Priority: optional
Architecture: $arch
Maintainer: Dex APT Repository <noreply@github.com>
Homepage: https://github.com/dexidp/dex
Depends: libc6, adduser, init-system-helpers
Description: Dex OpenID Connect identity provider
 Unofficial package built from the upstream Dex release tag.
EOF
dpkg-deb --build --root-owner-group package "dexidp_${package_version}_${arch}.deb"
dpkg-deb --field "dexidp_${package_version}_${arch}.deb" Package Version Architecture
