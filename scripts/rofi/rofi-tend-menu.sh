#!/bin/bash
# rofi-tend-menu.sh — Obsidian tending actions via rofi

VAULT="$HOME/github/obsidian-vault"
TEND="$VAULT/scripts/tend.py"
ALIAS_PICKER="$HOME/github/scripts/scripts/rofi/rofi-alias-picker.sh"

if [ ! -f "$TEND" ]; then
	notify-send "Tend" "Missing $TEND"
	exit 1
fi

entries=(
	"Revisit due notes|terminal|python3 $TEND --revisit"
	"Tend links|terminal|python3 $TEND"
	"Focus unlinked notes|terminal|python3 $TEND --links"
	"Fast link pass (no embeddings)|terminal|python3 $TEND --no-semantic"
	"Audit|terminal|python3 $TEND --stats --no-semantic"
	"Triage short notes|terminal|python3 $TEND --triage"
	"Refresh dashboard|terminal|python3 $TEND --refresh --no-semantic"
	"Open dashboard|obsidian|"
	"Rebuild semantic index|terminal|python3 $TEND --reindex"
	"Other script aliases|picker|"
)

labels=$(printf '%s\n' "${entries[@]}" | cut -d'|' -f1)
if [ "${1:-}" = "--list" ]; then
	printf '%s\n' "$labels"
	exit 0
fi
selected=$(printf '%s\n' "$labels" | rofi -dmenu -i -p "Tend" -matching fuzzy)

[ -z "$selected" ] && exit 0

entry=$(printf '%s\n' "${entries[@]}" | awk -F'|' -v name="$selected" '$1 == name {print; exit}')
[ -z "$entry" ] && exit 0

name=${entry%%|*}
rest=${entry#*|}
mode=${rest%%|*}
cmd=${rest#*|}

case "$mode" in
terminal)
	alacritty --title "Tend — $name" -e bash -lc "$cmd; echo; read -rp 'Press Enter to close.'"
	;;
obsidian)
	python3 "$TEND" --refresh --no-semantic >/dev/null
	xdg-open "obsidian://open?vault=$(basename "$VAULT")&file=Reflections/Tending.md"
	;;
picker)
	exec "$ALIAS_PICKER"
	;;
esac
