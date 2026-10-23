#!/bin/bash

# Define the scratchpad file path and a unique class name
NOTE_FILE="$HOME/.quicknote.md"
NOTE_CLASS="quicknote_nvim"

# If the file doesn't exist, create it
if [ ! -f "$NOTE_FILE" ]; then
    touch "$NOTE_FILE"
fi

# Use i3-msg to toggle the scratchpad window's visibility
i3-msg "[class=\"$NOTE_CLASS\"] scratchpad show" || \
# If the window isn't found, launch a new one
i3-msg "exec --no-startup-id alacritty --class \"$NOTE_CLASS\" -e nvim \"$NOTE_FILE\""
