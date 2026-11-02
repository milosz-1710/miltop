#!/usr/bin/env bash
set -euo pipefail

version="${1:?usage: build-arch.sh VERSION [OUTPUT_DIR]}"
output_dir="${2:-dist}"
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$output_dir" != /* ]]; then
    output_dir="$project_root/$output_dir"
fi
work_dir="$(mktemp -d)"
package_root="$work_dir/root"
archive="$output_dir/miltop-${version}-1-any.pkg.tar.zst"

mkdir -p "$output_dir"
install -Dpm0755 "$project_root/miltop.py" "$package_root/usr/bin/miltop"
install -Dpm0644 "$project_root/LICENSE" "$package_root/usr/share/licenses/miltop/LICENSE"
install -Dpm0644 "$project_root/README.md" "$package_root/usr/share/doc/miltop/README.md"
install -Dpm0644 "$project_root/CHANGELOG.md" "$package_root/usr/share/doc/miltop/CHANGELOG.md"

installed_size="$(du -sb "$package_root/usr" | cut -f1)"
cat >"$package_root/.PKGINFO" <<EOF
pkgname = miltop
pkgbase = miltop
pkgver = ${version}-1
pkgdesc = Lightweight tile-based terminal system monitor
url = https://github.com/milosz-1710/miltop
builddate = ${SOURCE_DATE_EPOCH:-$(date +%s)}
packager = miltop GitHub Actions
size = ${installed_size}
arch = any
license = GPL-3.0-or-later
depend = python
depend = python-psutil
optdepend = inxi: detailed RAM hardware identification
optdepend = nvidia-utils: NVIDIA GPU metrics
EOF

tar --zstd --sort=name --mtime="@${SOURCE_DATE_EPOCH:-0}" \
    --owner=0 --group=0 --numeric-owner -C "$package_root" -cf "$archive" .
printf '%s\n' "$archive"
