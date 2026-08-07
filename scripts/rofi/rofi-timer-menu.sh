#!/bin/bash
# rofi-timer-menu.sh
# Set, view, and cancel countdown timers via the timer-daemon socket.
# Saved presets in ~/.config/timers/presets can be started with a single click.

DAEMON="$HOME/.local/bin/timer-daemon"
PRESET_FILE="${TIMER_PRESETS_FILE:-$HOME/.config/timers/presets}"

send() {
	"$DAEMON" "$@"
}

fmt_duration() {
	python3 - "$1" <<'PYEOF'
import re, sys
raw = sys.argv[1].strip().lower()
if not raw:
    sys.exit(0)

def total(secs):
    print(secs)
    sys.exit(0)

if raw.isdigit():
    total(int(raw) * 60)  # bare number = minutes

parts = re.findall(r"(\d+)\s*(h|hr|hrs|m|min|mins|s|sec|secs)", raw)
if parts:
    secs = 0
    for val, unit in parts:
        val = int(val)
        if unit.startswith("h"):
            secs += val * 3600
        elif unit.startswith("m"):
            secs += val * 60
        else:
            secs += val
    total(secs)

# mm:ss or h:mm:ss
parts = re.findall(r"(\d+):(\d+)(?::(\d+))?", raw)
if parts:
    a, b, c = parts[0]
    secs = int(a) * 3600 + int(b) * 60 + (int(c) if c else 0)
    total(secs)

# raw seconds marker like "90sec"
sys.exit(1)
PYEOF
}

resolve_preset() {
	# resolve_preset NAME  -> echoes "NAME|DURATION" from the presets file
	local target="$1" name dur
	[ -f "$PRESET_FILE" ] || return 1
	while IFS= read -r line; do
		case "$line" in
			"" | \#*) continue ;;
		esac
		name="${line%%|*}"
		dur="${line#*|}"
		name="${name%"${name##*[![:space:]]}"}"  # trim trailing space
		if [ "$name" = "$target" ]; then
			printf '%s|%s' "$name" "$dur"
			return 0
		fi
	done < "$PRESET_FILE"
	return 1
}

# Build the menu: New Timer + saved presets + one cancel entry per active timer
presets=$(python3 -c '
import sys, os
path = os.path.expanduser(os.environ.get("TIMER_PRESETS_FILE", "~/.config/timers/presets"))
if not os.path.isfile(path):
    sys.exit(0)
for line in open(path):
    line = line.strip()
    if not line or line.startswith("#") or "|" not in line:
        continue
    name, dur = line.split("|", 1)
    dur = dur.strip()
    if dur:
        print(f"Set: {name.strip()}")
')

active=$(send list | python3 -c '
import json, sys
data = json.loads(sys.stdin.read())
for t in data.get("timers", []):
    if t["remaining"] <= 0:
        continue
    rem = t["remaining"]
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    label = t["label"] or f"timer {t['id']}"
    if h:
        label = f"{label} ({h}:{m:02d}:{s:02d})"
    else:
        label = f"{label} ({m:02d}:{s:02d})"
    print(f"Cancel: {label}")
')

menu="New Timer"
[ -n "$presets" ] && menu="$menu
── Presets ──
$presets"
[ -n "$active" ] && menu="$menu
── Active ──
$active"

choice=$(printf '%s\n' "$menu" | rofi -dmenu -p "Timer")

case "$choice" in
"" ) exit 0 ;;
"New Timer")
	# ask for minutes (or seconds with an "s" suffix)
	dur_input=$(rofi -dmenu -p "Duration (1h, 20m, 90s, 25 = minutes)")
	[ -z "$dur_input" ] && exit 0

	secs=$(fmt_duration "$dur_input")
	if [ -z "$secs" ] || [ "$secs" -le 0 ]; then
		notify-send "Timer" "Bad duration: $dur_input"
		exit 1
	fi

	label=$(rofi -dmenu -p "Label (optional)")
	send start "$secs" "$label"
	;;
"Set: "*)
	# single-click preset: start the recorded timer, reusing its label
	name="${choice#Set: }"
	if resolved=$(resolve_preset "$name"); then
		pname="${resolved%%|*}"
		pdur="${resolved#*|}"
		secs=$(fmt_duration "$pdur")
		if [ -n "$secs" ] && [ "$secs" -gt 0 ]; then
			send start "$secs" "$pname"
			notify-send "Timer" "Started: $pname"
		else
			notify-send "Timer" "Bad preset duration for $pname"
		fi
	fi
	;;
"Cancel: "*)
	id=$(send list | python3 -c '
import json, sys
data = json.loads(sys.stdin.read())
target = sys.argv[1]
for t in data.get("timers", []):
    if t["remaining"] <= 0:
        continue
    rem = t["remaining"]
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    label = t["label"] or f"timer {t['id']}"
    if h:
        label = f"{label} ({h}:{m:02d}:{s:02d})"
    else:
        label = f"{label} ({m:02d}:{s:02d})"
    if label == target:
        print(t["id"])
        break
' "$choice")
	[ -n "$id" ] && send stop "$id"
	;;
esac