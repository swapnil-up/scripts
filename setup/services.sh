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

# Timer daemon
if [ -f "$HOME/.local/bin/timer-daemon" ]; then
	if [ -f "$HOME/.config/systemd/user/timer-daemon.service" ]; then
		systemctl --user daemon-reload
		systemctl --user enable timer-daemon
		systemctl --user start timer-daemon
	else
		echo "  [WARN] timer-daemon.service not found — stow may not have run yet"
	fi
else
	echo "  [WARN] timer-daemon not linked — deploy-scripts may not have run yet"
fi

echo ">>> SERVICES_COMPLETE <<<"
