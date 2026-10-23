#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=manifest.sh
source "$SCRIPT_DIR/manifest.sh"

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
	DRY_RUN=true
fi

echo ">>> APT_START <<<"
echo "--- Installing APT Packages ---"

CODENAME=""
if [ -r /etc/os-release ]; then
	# shellcheck disable=SC1091
	. /etc/os-release
	CODENAME="${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}"
fi
if [ -z "$CODENAME" ]; then
	echo "ERROR: could not detect OS codename" >&2
	exit 1
fi

PACKAGES=(
	"${APT_CLI[@]}"
	"${APT_DESKTOP[@]}"
	"${APT_APPS[@]}"
	"${APT_BUILD[@]}"
	"${APT_DATABASE[@]}"
)

is_installable() {
	local candidate
	candidate="$(apt-cache policy "$1" 2>/dev/null | awk '/^  Candidate:/ {print $2; exit}')"
	[ -n "$candidate" ] && [ "$candidate" != "(none)" ]
}

install=()
skipped=()
for pkg in "${PACKAGES[@]}"; do
	if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
		continue
	fi
	if ! is_installable "$pkg"; then
		skipped+=("$pkg")
		continue
	fi
	install+=("$pkg")
done

for pkg in "${APT_OPTIONAL[@]}"; do
	if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
		continue
	fi
	if is_installable "$pkg"; then
		install+=("$pkg")
	else
		echo "  [SKIP] $pkg is not available on $CODENAME"
	fi
done

if [ "${#skipped[@]}" -gt 0 ]; then
	echo "  [SKIP] Not available on $CODENAME: ${skipped[*]}"
fi

if [ "${#install[@]}" -eq 0 ]; then
	echo "All APT packages already installed."
	echo ">>> APT_COMPLETE <<<"
	exit 0
fi

if [ "$DRY_RUN" = true ]; then
	echo "Would install ${#install[@]} package(s):"
	printf '  %s\n' "${install[@]}"
	echo ">>> APT_COMPLETE <<<"
	exit 0
fi

echo "Installing ${#install[@]} package(s)..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get install -y "${install[@]}"

echo ">>> APT_COMPLETE <<<"
