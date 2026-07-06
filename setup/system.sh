#!/bin/bash
set -euo pipefail

echo ">>> SYSTEM_START <<<"
echo "--- Configuring System Settings ---"

sudo groupadd --system uinput || true
sudo usermod -aG input $USER
sudo usermod -aG uinput $USER
echo 'KERNEL=="uinput", MODE="0660", GROUP="uinput", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-input.rules >/dev/null

# Brightness control (brightnessctl needs video group write access)
sudo usermod -aG video $USER

# Dark mode (GTK apps default to dark, no flash on launch)
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true
gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita-dark' 2>/dev/null || true

echo ">>> SYSTEM_COMPLETE <<<"
