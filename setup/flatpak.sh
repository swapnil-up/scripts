#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=manifest.sh
source "$SCRIPT_DIR/manifest.sh"

echo ">>> FLATPAK_START <<<"
echo "--- Configuring Flatpak ---"

if command -v snap &>/dev/null && snap list | grep -q "^flatpak "; then
	sudo snap remove flatpak
fi

if ! dpkg-query -W -f='${Status}' flatpak 2>/dev/null | grep -q "install ok installed"; then
	sudo apt-get install -y flatpak
fi
sudo flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

for app in "${FLATPAK_APPS[@]}"; do
	if flatpak list --app --columns=application | grep -qx "$app"; then
		echo "  [OK] $app already installed"
		continue
	fi
	echo "Installing $app..."
	flatpak install -y flathub "$app"
done

flatpak_exports="$HOME/.local/share/flatpak/exports/share"
if [[ ":$XDG_DATA_DIRS:" != *":$flatpak_exports:"* ]]; then
	export XDG_DATA_DIRS="$flatpak_exports:$XDG_DATA_DIRS"
fi

echo ">>> FLATPAK_COMPLETE <<<"
