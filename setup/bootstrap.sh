#!/bin/bash
set -euo pipefail

echo ">>> BOOTSTRAP_START <<<"
export DEBIAN_FRONTEND=noninteractive

# 0. Setup Logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$(cd "$SCRIPT_DIR/.." && pwd)/setup.log"
export LOG_FILE
echo "--- Logging setup to $LOG_FILE ---"
echo "Setup started at $(date)" > "$LOG_FILE"

# 1. Keep sudo alive
sudo -v
while true; do
	sudo -n true
	sleep 60
	kill -0 "$$" || exit
done 2>/dev/null &

# 2. Cleanup broken repo state first
echo "Cleaning up legacy repository conflicts..." | tee -a "$LOG_FILE"
sudo rm -f /etc/apt/sources.list.d/llvm-18.list* | tee -a "$LOG_FILE"
sudo rm -f /etc/apt/trusted.gpg.d/llvm-18.gpg | tee -a "$LOG_FILE"

# 3. Define execution order
SCRIPTS=(
	"repos.sh"      # External repositories
	"apt.sh"        # Main package installation
	"system.sh"     # udev, groups, etc.
	"languages.sh"  # Pyenv, NVM, Rust
	"kmp.sh"        # JDK 21, Android SDK, udev rules for KMP
	"php.sh"        # PHP CLI, extensions, Composer
	"source.sh"     # CMake, Clipmenu (in ~/github)
	"binaries.sh"   # Starship, Kanata, browsers, appimages
	"deploy-scripts.sh" # Symlink scripts/ → ~/.local/bin/
	"vault-scripts-link.sh" # Symlink vault-scripts → obsidian-vault
	"flatpak.sh"    # Flatpak & Obsidian
	"fonts.sh"      # Nerd fonts & emojis
	"piper.sh"      # Piper TTS (downloads model)
	"whisper.sh"    # Whisper.cpp (builds from source)
	"stow.sh"       # Linking dotfiles
	"services.sh"   # Enable user services (kanata, etc.)
)

# 4. State file for resuming interrupted bootstrap
STATE_DIR="$HOME/.local/state/setup"
mkdir -p "$STATE_DIR"

# 5. Execute scripts
for script in "${SCRIPTS[@]}"; do
	marker="${script%.sh}"
	if [ -f "$STATE_DIR/$marker" ]; then
		echo "--- Skipping $script (already completed) ---" | tee -a "$LOG_FILE"
		continue
	fi
	echo "--- Executing $script ---" | tee -a "$LOG_FILE"
	chmod +x "$SCRIPT_DIR/$script"
	if "$SCRIPT_DIR/$script" 2>&1 | tee -a "$LOG_FILE"; then
		touch "$STATE_DIR/$marker"
	else
		echo "--- $script FAILED (check $LOG_FILE) ---" | tee -a "$LOG_FILE"
		exit 1
	fi
done

# Clean up state on full success
rm -rf "$STATE_DIR"

echo ">>> BOOTSTRAP_COMPLETE <<<"
echo "Setup complete! Restart your shell."
