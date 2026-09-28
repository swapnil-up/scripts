#!/bin/bash
# rofi-timer-menu.sh
# Set, view, and cancel countdown timers via the timer-daemon socket.
# Saved presets in ~/.config/timers/presets can be started with a single click.

DAEMON="$HOME/.local/bin/timer-daemon"
PRESET_FILE="${TIMER_PRESETS_FILE:-$HOME/.config/timers/presets}"
LOG_FILE="${XDG_STATE_HOME:-$HOME/.local/state}/timer-daemon.log"

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

menu="New Timer
View History"
[ -n "$presets" ] && menu="$menu
── Presets ──
$presets"
[ -n "$active" ] && menu="$menu
── Active ──
$active"

choice=$(printf '%s\n' "$menu" | rofi -dmenu -p "Timer")

show_history() {
	# Show run history (newest first) in a read-only rofi view.
	# Arg $1: "View History" or "History: ..." — "View History" prompts for scope.
	scope="$1"
	if [ -z "$scope" ] || [ "$scope" = "View History" ]; then
		scope=$(printf 'History: Today\nHistory: All (last 100)\n' | rofi -dmenu -p "History")
		[ -z "$scope" ] && return 0
	fi
	if [ ! -f "$LOG_FILE" ]; then
		notify-send "Timer" "No history yet"
		return 0
	fi
	LOG_FILE="$LOG_FILE" SCOPE="$scope" python3 <<'PYEOF' | rofi -dmenu -p "Runs" -no-custom
import json, os
from datetime import date
log = os.environ.get("LOG_FILE", "")
scope = os.environ.get("SCOPE", "History: All (last 100)")
today = date.today().isoformat()
starts = []
try:
    with open(log) as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("event") != "start":
                continue
            starts.append(e)
except OSError:
    pass
if scope.startswith("History: Today"):
    starts = [e for e in starts if e.get("ts", "").startswith(today)]
else:
    starts = starts[-100:]
starts.reverse()
def fmt_dur(s):
    try:
        s = int(s)
    except (TypeError, ValueError):
        return "?"
    h, r = divmod(s, 3600)
    m, sec = divmod(r, 60)
    if h and m:
        return f"{h}h{m}m"
    if h:
        return f"{h}h"
    if m and sec:
        return f"{m}m{sec}s"
    if m:
        return f"{m}m"
    return f"{sec}s"
total = sum(int(e.get("duration", 0) or 0) for e in starts)
print(f"Today: {len(starts)} runs" if scope.startswith("History: Today") else f"Last {len(starts)} runs, {fmt_dur(total)} total")
for e in starts:
    ts = e.get("ts", "")[:16].replace("T", " ")
    label = e.get("label") or "timer"
    print(f"{ts}  {label}  {fmt_dur(e.get('duration', 0))}")
PYEOF
}

case "$choice" in
"" ) exit 0 ;;
"View History"|"History: "*)
	show_history "$choice"
	;;
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