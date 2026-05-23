#!/bin/bash

TODO_FILE="$HOME/.local/share/todos/todo.txt"

# Rofi prompt for new todo
NEW_TODO=$(rofi -dmenu -p "Add todo:" -lines 0)

# If user entered something, append it
if [ -n "$NEW_TODO" ]; then
	echo "$NEW_TODO" >>"$TODO_FILE"
	notify-send "Todo added" "$NEW_TODO"
fi
