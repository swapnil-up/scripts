#!/bin/bash

TODO_FILE="$HOME/.local/share/todos/todo.txt"
DONE_FILE="$HOME/.local/share/todos/completed.txt"

# Show current todos in rofi
SELECTED=$(cat "$TODO_FILE" | rofi -dmenu -p "Complete todo:")

if [ -n "$SELECTED" ]; then
	# Add to done file with timestamp
	echo "$(date +%Y-%m-%d) - $SELECTED" >>"$DONE_FILE"

	# Remove from active todos (using grep -v for exact match)
	grep -vF "$SELECTED" "$TODO_FILE" >"$TODO_FILE.tmp"
	mv "$TODO_FILE.tmp" "$TODO_FILE"

	notify-send "Todo completed" "$SELECTED"
fi
