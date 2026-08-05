#!/bin/bash
# rofi-timer-menu.sh
# Set, view, and cancel countdown timers via the timer-daemon socket.

DAEMON="$HOME/.local/bin/timer-daemon"

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

# Build the menu: New Timer + one cancel entry per active timer
menu=$(send list | python3 -c '
import json, sys
data = json.loads(sys.stdin.read())
lines = ["New Timer"]
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
    lines.append(f"Cancel: {label}")
print("\n".join(lines))
')

choice=$(echo "$menu" | rofi -dmenu -p "Timer")

case "$choice" in
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
Cancel:*)
	id=$(send list | python3 -c '
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
    if label == sys.argv[1]:
        print(t["id"])
        break
' "$choice")
	[ -n "$id" ] && send stop "$id"
	;;
esac
