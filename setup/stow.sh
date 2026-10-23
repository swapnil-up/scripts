#!/bin/bash
set -euo pipefail

echo ">>> STOW_START <<<"
echo "--- Linking Configurations with Stow ---"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(cd "$SCRIPT_DIR/../config" && pwd)"
BACKUP_ROOT="$HOME/.local/state/setup-backup"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
	DRY_RUN=true
fi

backup_count=0
prune_count=0
stow_count=0

# Return the symlink target with a missing final component still resolved.
resolve_path() {
	realpath -m "$1" 2>/dev/null
}

backup_path() {
	local path="$1"
	local rel="${path#"$HOME"/}"
	local dest="$BACKUP_DIR/$rel"

	if $DRY_RUN; then
		echo "  [WOULD BACKUP] $path -> $dest"
		backup_count=$((backup_count + 1))
		return
	fi

	mkdir -p "$(dirname "$dest")"
	mv "$path" "$dest"
	echo "  [BACKUP] $path -> $dest"
	backup_count=$((backup_count + 1))
}

# Remove a conflict without deleting data: symlinks are moved as links, real
# files/directories are moved whole into the timestamped backup directory.
prepare_target() {
	local target="$1"
	local source="$2"
	local rel="${target#"$HOME"/}"
	local cur="$HOME"
	local part
	local -a parts=()

	IFS='/' read -r -a parts <<<"$rel"
	local last=$((${#parts[@]} - 1))

	for i in "${!parts[@]}"; do
		part="${parts[i]}"
		cur="$cur/$part"

		if [ "$i" -lt "$last" ]; then
			if [ -L "$cur" ]; then
				# A stow-managed parent is fine; stow will unfold it.
				case "$(resolve_path "$cur")" in
				"$CONFIG_DIR"/*) return 0 ;;
				esac
				# A parent symlink points somewhere else. Move the link
				# itself, then recreate a real directory for stow.
				backup_path "$cur"
				$DRY_RUN || mkdir -p "$cur"
				return 0
			fi
			if [ -e "$cur" ] && [ ! -d "$cur" ]; then
				backup_path "$cur"
				$DRY_RUN || mkdir -p "$cur"
				return 0
			fi
			continue
		fi

		# Final path component.
		if [ -L "$cur" ]; then
			if [ "$(resolve_path "$cur")" = "$source" ]; then
				return 0
			fi
			backup_path "$cur"
			return 0
		fi

		if [ -e "$cur" ]; then
			if [ -d "$cur" ] && [ -d "$source" ]; then
				return 0
			fi
			backup_path "$cur"
		fi
	done
}

prepare_package() {
	while IFS= read -r -d '' entry; do
		local rel="${entry#"$folder"/}"
		prepare_target "$HOME/$rel" "$CONFIG_DIR/$folder/$rel"
	done < <(find "$folder" -mindepth 1 \( -type f -o -type l \) -print0)

	while IFS= read -r -d '' entry; do
		local rel="${entry#"$folder"/}"
		local target="$HOME/$rel"
		if [ -L "$target" ] && [ "$(resolve_path "$target")" != "$CONFIG_DIR/$folder/$rel" ]; then
			backup_path "$target"
		elif [ -e "$target" ] && [ ! -d "$target" ]; then
			backup_path "$target"
		fi
	done < <(find "$folder" -mindepth 1 -type d -print0)
}

prune_dangling() {
	local link target resolved
	while IFS= read -r -d '' link; do
		target="$(readlink "$link")"
		case "$target" in
		/*) resolved="$(resolve_path "$target")" ;;
		*) resolved="$(resolve_path "$(dirname "$link")/$target")" ;;
		esac
		[ -n "$resolved" ] || continue
		case "$resolved" in
		"$CONFIG_DIR"/*) ;;
		*) continue ;;
		esac
		if [ ! -e "$link" ]; then
			if $DRY_RUN; then
				echo "  [WOULD PRUNE] $link"
			else
				rm -f "$link"
				echo "  [PRUNE] $link"
			fi
			prune_count=$((prune_count + 1))
		fi
	done < <({
		find "$HOME" -xdev -maxdepth 1 -type l -print0 2>/dev/null
		find "$HOME/.config" "$HOME/.agents" -xdev -maxdepth 7 -type l -print0 2>/dev/null
		find "$HOME/.local/bin" -xdev -maxdepth 1 -type l -print0 2>/dev/null
	} | sort -zu)
}

deploy_vscode_settings() {
	local user_dir="$HOME/.config/Code/User"
	local base="$CONFIG_DIR/vscode/.config/Code/User/settings.base.json"
	local local_file="$user_dir/settings.local.json"
	local target="$user_dir/settings.json"

	[ -f "$base" ] || return 0

	if $DRY_RUN; then
		echo "  [WOULD GENERATE] $target (base + ${local_file##*/})"
		return
	fi

	mkdir -p "$user_dir"
	python3 "$SCRIPT_DIR/lib/jsonc-merge.py" "$base" "$local_file" >"$target.tmp"
	[ -L "$target" ] && rm -f "$target"
	mv "$target.tmp" "$target"
	echo "  [GENERATE] $target"
}

cd "$CONFIG_DIR"

for folder in */; do
	folder=${folder%/}

	# Never replace user directories with folded symlinks. Individual file
	# links also keep packages from fighting over shared directories.
	stow_opts=(--no-folding --ignore='README\.md')

	prepare_package

	if $DRY_RUN; then
		echo "  [WOULD STOW] $folder"
		continue
	fi

	# Verify that all conflicts were handled before touching the tree.
	if ! stow -n -t "$HOME" "${stow_opts[@]}" "$folder" >/tmp/stow-preflight.$$ 2>&1; then
		echo "  [ERROR] unresolved conflict while stowing $folder:" >&2
		sed 's/^/    /' /tmp/stow-preflight.$$ >&2
		rm -f /tmp/stow-preflight.$$
		exit 1
	fi
	rm -f /tmp/stow-preflight.$$

	echo "  [LINK] Stowing $folder..."
	stow -R -t "$HOME" "${stow_opts[@]}" "$folder"
	stow_count=$((stow_count + 1))
done

deploy_vscode_settings
prune_dangling

if $DRY_RUN; then
	echo "Dry run: $backup_count conflict(s) would be backed up, $prune_count stale link(s) pruned."
else
	echo "Stowed $stow_count package(s); backed up $backup_count conflict(s); pruned $prune_count stale link(s)."
	if [ "$backup_count" -gt 0 ]; then
		echo "Backups: $BACKUP_DIR"
	fi
fi

echo ">>> STOW_COMPLETE <<<"
