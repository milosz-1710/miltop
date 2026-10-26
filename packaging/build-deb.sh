#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="${1:-}"
output_dir="${2:-${project_root}/dist}"

if [[ ! "$version" =~ ^[0-9]+([.][0-9]+){1,2}([+~][0-9A-Za-z.-]+)?$ ]]; then
    echo "Usage: $0 VERSION [OUTPUT_DIR]" >&2
    exit 2
fi
if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "dpkg-deb is required to build the Debian package" >&2
    exit 1
fi

work_dir="$(mktemp -d "${TMPDIR:-/tmp}/miltop-deb.XXXXXX")"
trap 'rm -rf -- "$work_dir"' EXIT
package_root="${work_dir}/miltop_${version}_all"

install -Dm0755 "${project_root}/miltop.py" "${package_root}/usr/bin/miltop"
install -Dm0644 "${project_root}/LICENSE" "${package_root}/usr/share/doc/miltop/LICENSE"
install -Dm0644 "${project_root}/README.md" "${package_root}/usr/share/doc/miltop/README.md"
install -Dm0644 "${project_root}/CHANGELOG.md" "${package_root}/usr/share/doc/miltop/CHANGELOG.md"
install -d "${package_root}/DEBIAN"

cat >"${package_root}/DEBIAN/control" <<EOF
Package: miltop
Version: ${version}
Section: utils
Priority: optional
Architecture: all
Maintainer: Miłosz <79249752+milosz-1710@users.noreply.github.com>
Depends: python3 (>= 3.10), python3-psutil
Homepage: https://github.com/milosz-1710/miltop
Description: lightweight tile-based terminal system monitor
 miltop displays CPU, memory, disk, network and process information in a
 keyboard- and mouse-friendly terminal dashboard.
EOF

mkdir -p "$output_dir"
dpkg-deb --root-owner-group --build "$package_root" "${output_dir}/miltop_${version}_all.deb"
