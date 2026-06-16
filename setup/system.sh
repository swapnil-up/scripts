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

echo ">>> SYSTEM_COMPLETE <<<"
