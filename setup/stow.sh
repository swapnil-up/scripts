#!/bin/bash
set -euo pipefail

echo ">>> STOW_START <<<"
echo "--- Linking Configurations with Stow ---"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(cd "$SCRIPT_DIR/../config" && pwd)"

cd "$CONFIG_DIR"

for folder in */; do
	folder=${folder%/}

	pkg_source="$(cd "$CONFIG_DIR/$folder" && pwd -P)"

	# 1) Remove real directories that block stow folding.
	#    Only clean up if the parent dir is itself a stow target (i.e. also
	#    in the package tree) -- this avoids touching shared dirs like ~/.config
	#    which are real dirs that stow correctly creates symlinks *inside*.
	while IFS= read -r -d '' pkgdir; do
		relpath="${pkgdir#$folder/}"
		[ "$relpath" = "$folder" ] && continue
		conflict="$HOME/$relpath"

		# Skip if parent is a real (non-stow-managed) directory.
		# Stow creates symlinks inside these, not replacements.
		parent="$(dirname "$conflict")"
		if [ -d "$parent" ] && ! [ -L "$parent" ]; then
			continue
		fi

		if [ -d "$conflict" ] && ! [ -L "$conflict" ]; then
			resolved=$(readlink -f "$conflict" 2>/dev/null || true)
			if [ "$resolved" = "$pkg_source/$relpath" ]; then
				continue
			fi
			echo "  [CLEANUP] Removing conflicting directory: $conflict"
			rm -rf "$conflict"
		fi
	done < <(find "$folder" -mindepth 1 -type d -print0)

	# 2) Remove real files that conflict with stow target files.
	while IFS= read -r -d '' pkgfile; do
		relpath="${pkgfile#$folder/}"
		conflict="$HOME/$relpath"
		if [ -e "$conflict" ] && ! [ -L "$conflict" ]; then
			resolved=$(readlink -f "$conflict" 2>/dev/null || true)
			pkg_real="$(cd "$(dirname "$CONFIG_DIR/$pkgfile")" && pwd -P)/$(basename "$pkgfile")"
			if [ "$resolved" = "$pkg_real" ]; then
				continue
			fi
			echo "  [CLEANUP] Removing conflicting target: $conflict"
			rm -f "$conflict"
		fi
	done < <(find "$folder" -type f -print0)

	no_fold=""
	if [ "$folder" = "vscode" ]; then
		no_fold="--no-folding"
	fi

	echo "  [LINK] Stowing $folder..."
	stow -R -t "$HOME" $no_fold "$folder"

	# 3) Remove stale symlinks left behind by removed package files.
	while IFS= read -r -d '' syml; do
		if [ -L "$syml" ] && ! [ -e "$syml" ]; then
			echo "  [CLEANUP] Removing stale symlink: $syml"
			rm -f "$syml"
		fi
	done < <(find "$folder" -type l -print0)
done

echo ">>> STOW_COMPLETE <<<"
