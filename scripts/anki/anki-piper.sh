#!/bin/bash
set -euo pipefail

# Configuration
DECK_NAME="Testing"
NOTE_TYPE="Basic"
LOG_FILE=~/.anki_debug.log

# 1. Capture highlight IMMEDIATELY (before focus shifts)
highlighted_text=$(xclip -o -sel primary 2>/dev/null || xclip -o -sel clipboard 2>/dev/null)

# 2. Get Window Info
sleep 0.2
active_window_id=$(xprop -root _NET_ACTIVE_WINDOW | awk '{print $5}')

if [[ $active_window_id != "0x0" && -n $active_window_id ]]; then
	# Try UTF8 name, then String name, then Class
	source_name=$(xprop -id "$active_window_id" _NET_WM_NAME 2>/dev/null | cut -d'=' -f2 | tr -d '"' | sed 's/^ //')
	[[ -z $source_name ]] && source_name=$(xprop -id "$active_window_id" WM_NAME 2>/dev/null | cut -d'=' -f2 | tr -d '"' | sed 's/^ //')
	[[ -z $source_name ]] && source_name=$(xprop -id "$active_window_id" WM_CLASS 2>/dev/null | awk -F '"' '{print $4}')
fi
source_name="${source_name:-Unknown Application}"

# 3. Check Anki & Launch silently if needed
if ! curl -s --max-time 0.1 http://localhost:8765 >/dev/null; then
	# setsid detaches it from the current process group to prevent hang
	setsid anki >/dev/null 2>&1 &
	# Wait for AnkiConnect to be ready (up to 8s)
	for i in {1..20}; do
		curl -s localhost:8765 -d '{"action":"version","version":6}' | grep -q '"error":null' && break
		sleep 0.4
	done
fi

# 4. Construct Payload
current_datetime=$(date '+%Y-%m-%d %H:%M')
context_payload="<div style='color:gray; font-size:0.8em;'>Source: $source_name ($current_datetime)</div><br><b>$highlighted_text</b>"

payload=$(jq -n \
	--arg deck "$DECK_NAME" \
	--arg note "$NOTE_TYPE" \
	--arg context "$context_payload" \
	'{
    "action": "guiAddCards",
    "version": 6,
    "params": {
      "note": {
        "deckName": $deck,
        "modelName": $note,
        "fields": { "Front": "", "Back": "", "Context": $context },
        "tags": ["script-capture"]
      }
    }
  }')

# 5. Send and Focus
response=$(curl -s -X POST -d "$payload" http://localhost:8765)

# If in i3, move to the Anki window automatically to avoid the "red" urgency hint
i3-msg '[class="Anki" title="Add"] focus' >/dev/null 2>&1

echo "$current_datetime: Dispatched highlight" >>"$LOG_FILE"
