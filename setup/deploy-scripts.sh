#!/bin/bash
set -euo pipefail

echo ">>> DEPLOY_SCRIPTS_START <<<"
echo "--- Symlinking repo scripts to ~/.local/bin ---"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCRIPTS_SRC="$REPO_ROOT/scripts"
TARGET_DIR="$HOME/.local/bin"

mkdir -p "$TARGET_DIR"

for entry in "$SCRIPTS_SRC"/*; do
	name=$(basename "$entry")
	case "$name" in
		AGENTS.md|README.md|anki|editor|espanso|python|rofi|snippets|template|utils|vault-scripts)
			continue
			;;
	esac
	target="$TARGET_DIR/$name"
	if [ -L "$target" ] && [ "$(readlink "$target")" = "$entry" ]; then
		echo "  [OK] $name already linked"
	elif [ -e "$target" ]; then
		echo "  [SKIP] $name: $target exists and is not our symlink"
	else
		ln -s "$entry" "$target"
		echo "  [LINK] $name -> $entry"
	fi
done

echo ">>> DEPLOY_SCRIPTS_COMPLETE <<<"
