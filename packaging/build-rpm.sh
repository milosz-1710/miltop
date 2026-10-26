#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="${1:-}"
output_dir="${2:-${project_root}/dist}"

if [[ ! "$version" =~ ^[0-9]+([.][0-9]+){1,2}$ ]]; then
    echo "Usage: $0 VERSION [OUTPUT_DIR]" >&2
    exit 2
fi
if ! command -v rpmbuild >/dev/null 2>&1; then
    echo "rpmbuild is required to build the RPM package" >&2
    exit 1
fi

work_dir="$(mktemp -d "${TMPDIR:-/tmp}/miltop-rpm.XXXXXX")"
trap 'rm -rf -- "$work_dir"' EXIT
top_dir="${work_dir}/rpmbuild"
mkdir -p "${top_dir}"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

install -m0644 "${project_root}/miltop.py" "${top_dir}/SOURCES/miltop.py"
install -m0644 "${project_root}/LICENSE" "${top_dir}/SOURCES/LICENSE"
install -m0644 "${project_root}/README.md" "${top_dir}/SOURCES/README.md"
install -m0644 "${project_root}/CHANGELOG.md" "${top_dir}/SOURCES/CHANGELOG.md"

rpmbuild -bb "${project_root}/packaging/rpm/miltop.spec" \
    --define "_topdir ${top_dir}" \
    --define "miltop_version ${version}"

mkdir -p "$output_dir"
find "${top_dir}/RPMS" -type f -name '*.rpm' -exec cp -v {} "$output_dir/" \;
