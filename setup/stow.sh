#!/bin/bash
set -euo pipefail

echo ">>> STOW_START <<<"
echo "--- Linking Configurations with Stow ---"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(cd "$SCRIPT_DIR/../config" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$CONFIG_DIR"

	for folder in */; do
		folder=${folder%/}

		# Remove any regular file in $HOME that conflicts with this package
		# but skip files that resolve inside the repo (avoids deleting
		# actual repo files when a parent dir is a stow symlink into the repo)
		find "$folder" -type f | while read -r pkgfile; do
			relpath="${pkgfile#$folder/}"
			conflict="$HOME/$relpath"
			if [ -e "$conflict" ] && ! [ -L "$conflict" ]; then
				resolved=$(readlink -f "$conflict" 2>/dev/null)
				if [[ "$resolved" == "$REPO_ROOT"* ]]; then
					continue
				fi
				echo "  [CLEANUP] Removing conflicting target: $conflict"
				rm -rf "$conflict"
			fi
		done

		no_fold=""
		if [ "$folder" = "vscode" ]; then
			no_fold="--no-folding"
		fi

		echo "  [LINK] Stowing $folder..."
		stow -R -t "$HOME" $no_fold "$folder"
	done

echo ">>> STOW_COMPLETE <<<"
