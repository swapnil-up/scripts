#!/bin/bash
# rofi-todo-add.sh
# Unified todo management

TODO_FILE="$HOME/.local/share/todos/todo.txt"
COMPLETED_FILE="$HOME/.local/share/todos/completed.txt"

mkdir -p "$(dirname "$TODO_FILE")"
touch "$TODO_FILE"
touch "$COMPLETED_FILE"

trigger="$1"
inline_text="$2"

# --- Helpers ---
launch_rofi_selection() {
	rofi -dmenu -i -p "$2" -lines 0
}

notify() {
	notify-send "$1" "$2"
}

# --- Actions ---
case "$trigger" in
t)
	if [ -n "$inline_text" ]; then
		new_todo="$inline_text"
	else
		new_todo=$(rofi -dmenu -p "Add todo" -lines 0)
	fi

	if [ -n "$new_todo" ]; then
		timestamp=$(date "+%Y-%m-%d %H:%M")
		echo "[ ] $timestamp - $new_todo" >>"$TODO_FILE"
		notify-send "✓ Todo Added" "$new_todo"
	fi
	;;

	tt)
	# Toggle completion
	selected=$(cat -n "$TODO_FILE" | rofi -dmenu -i -p "Toggle todo" -lines 0)
	[ -z "$selected" ] && exit 0
	line_num=$(echo "$selected" | awk '{print $1}')
	line=$(sed -n "${line_num}p" "$TODO_FILE")
	if echo "$line" | grep -q "^\[ \]"; then
		new_line=$(echo "$line" | sed 's/^\[ \]/[x]/')
		sed -i "${line_num}s|.*|$new_line|" "$TODO_FILE"
		notify "✓ Todo completed" "Marked as done"
	elif echo "$line" | grep -q "^\[x\]"; then
		new_line=$(echo "$line" | sed 's/^\[x\]/[ ]/')
		sed -i "${line_num}s|.*|$new_line|" "$TODO_FILE"
		notify "↻ Todo reopened" "Marked as not done"
	fi
	;;

tr)
	# Remove todo
	selected=$(cat -n "$TODO_FILE" | rofi -dmenu -i -p "Remove todo" -lines 0)
	[ -z "$selected" ] && exit 0
	line_num=$(echo "$selected" | awk '{print $1}')
	sed -i "${line_num}d" "$TODO_FILE"
	notify "🗑 Todo removed" "Deleted from list"
	;;

ta)
	# Archive completed todos
	grep "^\[x\]" "$TODO_FILE" >>"$COMPLETED_FILE"
	grep -v "^\[x\]" "$TODO_FILE" >"${TODO_FILE}.tmp" && mv "${TODO_FILE}.tmp" "$TODO_FILE"
	count=$(grep -c "^\[x\]" "$COMPLETED_FILE")
	notify "🗄 Archived todos" "Moved $count completed todos"
	;;

*)
	notify "❌ Unknown command" "$trigger"
	;;
esac
