#!/usr/bin/env bash
set -euo pipefail

DECK="Testing"
LOG=~/.anki_review.log

echo "---- $(date) ----" >"$LOG"

# Capture workspace immediately
CURRENT_WS=$(i3-msg -t get_workspaces | jq -r '.[] | select(.focused==true).name')

anki_running=false
pgrep -x anki >/dev/null && anki_running=true

# Launch Anki only if needed
if [ "$anki_running" = false ]; then
	echo "Cold start" >>"$LOG"
	anki &
	# Only cold start waits
	for i in {1..20}; do
		curl -s localhost:8765 -d '{"action":"version","version":6}' | grep -q '"error":null' && break
		sleep 0.4
	done
else
	echo "Hot start" >>"$LOG"
fi

# Fire review immediately
payload=$(jq -n --arg deck "$DECK" '{
  action: "guiDeckReview",
  version: 6,
  params: { name: $deck }
}')

curl -s -X POST -d "$payload" http://localhost:8765 >>"$LOG"

# Focus & fullscreen immediately
ANKI_WIN=$(xdotool search --class anki | head -n1)

if [ -n "$ANKI_WIN" ]; then
	i3-msg "[id=$ANKI_WIN] move to workspace \"$CURRENT_WS\""
	i3-msg "[id=$ANKI_WIN] focus"
	i3-msg "[id=$ANKI_WIN] fullscreen enable"
	# xdotool key space
fi
