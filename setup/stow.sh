#!/bin/bash
set -euo pipefail

echo ">>> STOW_START <<<"
echo "--- Linking Configurations with Stow ---"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(cd "$SCRIPT_DIR/../config" && pwd)"

cd "$CONFIG_DIR"

	for folder in */; do
		folder=${folder%/}
		if [ -d "$folder/.config" ]; then
			TARGET="$HOME/.config/$folder"
		elif [ -f "$folder/.bashrc" ]; then
			TARGET="$HOME/.bashrc"
		elif [ -f "$folder/.zshrc" ]; then
			TARGET="$HOME/.zshrc"
		elif [ -f "$folder/.profile" ]; then
			TARGET="$HOME/.profile"
		else
			TARGET="$HOME/.$folder"
		fi

	if [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
		CURRENT_LINK=$(readlink -f "$TARGET" 2>/dev/null || echo "")
		if [[ $CURRENT_LINK != *"/github/scripts/"* ]]; then
			echo "  [CLEANUP] Removing conflicting target: $TARGET"
			rm -rf "$TARGET"
		fi
	fi

	echo "  [LINK] Stowing $folder..."
	stow -R -t "$HOME" "$folder"
done

echo ">>> STOW_COMPLETE <<<"
