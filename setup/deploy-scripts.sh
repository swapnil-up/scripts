#!/bin/bash
set -euo pipefail

echo ">>> DEPLOY_SCRIPTS_START <<<"
echo "--- Symlinking repo scripts to ~/.local/bin ---"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCRIPTS_SRC="$REPO_ROOT/scripts"
TARGET_DIR="$HOME/.local/bin"

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
	DRY_RUN=true
fi

mkdir -p "$TARGET_DIR"

linked=0
removed=0

resolves_into_repo() {
	local resolved
	resolved="$(readlink -m "$1" 2>/dev/null)" || return 1
	case "$resolved" in
	"$SCRIPTS_SRC"/*) return 0 ;;
	*) return 1 ;;
	esac
}

# Remove links that point into the repo but whose source is gone.
while IFS= read -r -d '' target; do
	resolves_into_repo "$target" || continue
	[ -e "$target" ] && continue
	if $DRY_RUN; then
		echo "  [WOULD PRUNE] $(basename "$target")"
	else
		rm -f "$target"
		echo "  [PRUNE] $(basename "$target")"
	fi
	removed=$((removed + 1))
done < <(find "$TARGET_DIR" -maxdepth 1 -type l -print0)

for entry in "$SCRIPTS_SRC"/*; do
	name=$(basename "$entry")
	case "$name" in
	AGENTS.md | README.md | anki | editor | espanso | python | rofi | snippets | template | utils | vault-scripts | nepali)
		continue
		;;
	esac
	target="$TARGET_DIR/$name"

	if [ -L "$target" ]; then
		current="$(readlink "$target")"
		if [ "$current" = "$entry" ]; then
			echo "  [OK] $name already linked"
			continue
		fi
		if resolves_into_repo "$target"; then
			if $DRY_RUN; then
				echo "  [WOULD RELINK] $name -> $entry"
			else
				rm -f "$target"
				ln -s "$entry" "$target"
				echo "  [RELINK] $name -> $entry"
			fi
			linked=$((linked + 1))
			continue
		fi
		if [ ! -e "$target" ]; then
			echo "  [SKIP] $name: dangling symlink to $(readlink "$target")"
		else
			echo "  [SKIP] $name: $target exists and is not our symlink"
		fi
		continue
	fi

	if [ -e "$target" ]; then
		echo "  [SKIP] $name: $target exists and is not our symlink"
		continue
	fi

	if $DRY_RUN; then
		echo "  [WOULD LINK] $name -> $entry"
	else
		ln -s "$entry" "$target"
		echo "  [LINK] $name -> $entry"
	fi
	linked=$((linked + 1))
done

if $DRY_RUN; then
	echo "Dry run: $linked link(s) would be created or repaired, $removed stale link(s) pruned."
else
	echo "Linked/repaired $linked script(s); pruned $removed stale link(s)."
fi

echo ">>> DEPLOY_SCRIPTS_COMPLETE <<<"
