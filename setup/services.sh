#!/bin/bash
set -euo pipefail

echo ">>> SERVICES_START <<<"
echo "--- Enabling User Services ---"

has_group() {
	id -nG | tr ' ' '\n' | grep -qx "$1"
}

# Kanata needs uinput/input group membership in the current session.
if command -v kanata &>/dev/null; then
	if [ -f "$HOME/.config/systemd/user/kanata.service" ]; then
		systemctl --user daemon-reload
		systemctl --user enable kanata
		if has_group uinput && has_group input; then
			if ! systemctl --user start kanata; then
				echo "  [WARN] kanata failed to start — check: journalctl --user -u kanata"
			fi
		else
			echo "  [WARN] uinput/input group not active in this session."
			echo "         Log out and back in, then run: systemctl --user start kanata"
		fi
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
		if ! systemctl --user start timer-daemon; then
			echo "  [WARN] timer-daemon failed to start — check: journalctl --user -u timer-daemon"
		fi
	else
		echo "  [WARN] timer-daemon.service not found — stow may not have run yet"
	fi
else
	echo "  [WARN] timer-daemon not linked — deploy-scripts may not have run yet"
fi

echo ">>> SERVICES_COMPLETE <<<"
