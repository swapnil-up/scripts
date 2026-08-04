#!/bin/bash
set -euo pipefail

echo ">>> VAULT_SCRIPTS_LINK_START <<<"
echo "--- Linking vault-scripts into obsidian-vault ---"

VAULT_DIR="$HOME/github/obsidian-vault"
SCRIPTS_SRC="$HOME/github/scripts/scripts/vault-scripts"
VAULT_SCRIPTS_DIR="$VAULT_DIR/scripts"

if [ ! -d "$VAULT_DIR" ]; then
	echo "  [SKIP] Obsidian vault not cloned yet at $VAULT_DIR"
	echo ">>> VAULT_SCRIPTS_LINK_COMPLETE <<<"
	exit 0
fi

mkdir -p "$VAULT_SCRIPTS_DIR"

for file in incremental.py move_unfinished.py README.md; do
	src="$SCRIPTS_SRC/$file"
	target="$VAULT_SCRIPTS_DIR/$file"

	if [ ! -f "$src" ]; then
		echo "  [SKIP] Source $src not found"
		continue
	fi

	if [ -L "$target" ] && [ "$(readlink "$target")" = "$src" ]; then
		echo "  [OK] $file already linked"
		continue
	fi

	if [ -e "$target" ] || [ -L "$target" ]; then
		rm -f "$target"
		echo "  [RM] Removed existing $target"
	fi

	ln -s "$src" "$target"
	echo "  [LINK] $file -> $src"
done

echo ">>> VAULT_SCRIPTS_LINK_COMPLETE <<<"