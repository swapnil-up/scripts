#!/bin/bash
set -euo pipefail

echo ">>> SYSTEM_START <<<"
echo "--- Configuring System Settings ---"

sudo groupadd --system uinput || true
sudo usermod -aG input "$USER"
sudo usermod -aG uinput "$USER"
echo 'KERNEL=="uinput", MODE="0660", GROUP="uinput", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-input.rules >/dev/null

# GoPro auto-ingest rule. udev does not expand variables, so substitute them
# while installing from the tracked template.
GOPRO_SRC="$HOME/github/scripts/scripts/editor/99-gopro.rules"
if [ -f "$GOPRO_SRC" ]; then
	sed -e "s|@HOME@|$HOME|g" -e "s|@USER@|$USER|g" "$GOPRO_SRC" |
		sudo tee /etc/udev/rules.d/99-gopro.rules >/dev/null
	sudo chmod 0644 /etc/udev/rules.d/99-gopro.rules
fi
sudo udevadm control --reload-rules
sudo udevadm trigger

# Brightness control (brightnessctl needs video group write access)
sudo usermod -aG video "$USER"

# Dark mode (GTK apps default to dark, no flash on launch)
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true
gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita-dark' 2>/dev/null || true

# Linger: allow systemd user services to start on boot (kanata, etc.)
sudo loginctl enable-linger "$USER" 2>/dev/null || true

echo ">>> SYSTEM_COMPLETE <<<"
