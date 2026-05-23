#!/bin/bash
# rofi-todo-menu.sh
# Main menu for todo operations

choice=$(echo -e "Add Todo\nToggle Todo\nRemove Todo\nView All" | rofi -dmenu -p "Todo Manager")

TODO_SCRIPT="$HOME/github/scripts/scripts/rofi/rofi-todo-add.sh"

case "$choice" in
"Add Todo")
	$TODO_SCRIPT t
	;;
"Toggle Todo")
	$TODO_SCRIPT tt
	;;
"Remove Todo")
	$TODO_SCRIPT tr
	;;
"View All")
	# Show all todos in a notification or terminal
	todos=$(cat "$HOME/.local/share/todos/todo.txt")
	notify-send "All Todos" "$todos"
	;;
esac
