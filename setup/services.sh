#!/bin/bash
set -euo pipefail

echo ">>> SERVICES_START <<<"
echo "--- Enabling User Services ---"

# Kanata
if command -v kanata &>/dev/null; then
	if [ -f "$HOME/.config/systemd/user/kanata.service" ]; then
		systemctl --user daemon-reload
		systemctl --user enable kanata
		systemctl --user start kanata
	else
		echo "  [WARN] kanata.service not found — stow may not have run yet"
	fi
else
	echo "  [WARN] kanata binary not found, skipping service"
fi

echo ">>> SERVICES_COMPLETE <<<"
