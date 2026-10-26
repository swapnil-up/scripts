#!/bin/bash
# rofi-shutdown-menu.sh
# Delayed shutdown protocol: schedule, cancel, or extend a poweroff timer.
# Canceling and extending require a typed reason, which timer-daemon logs.

DAEMON="${TIMER_DAEMON:-$HOME/.local/bin/timer-daemon}"
DEFAULT_SECS=60
ADD_SECS=300
ADD_LONG_SECS=900

notify() {
	notify-send -u critical -a "Shutdown" -t 12000 "$1" "$2"
}

fmt() {
	local total=$1 h m s
	h=$((total / 3600))
	total=$((total % 3600))
	m=$((total / 60))
	s=$((total % 60))
	if [ "$h" -gt 0 ]; then
		printf '%d:%02d:%02d' "$h" "$m" "$s"
	else
		printf '%02d:%02d' "$m" "$s"
	fi
}

query_active() {
	"$DAEMON" list 2>/dev/null | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for t in data.get("timers", []):
    if t.get("action") == "poweroff" and t.get("remaining", 0) > 0:
        print(t["id"], t["remaining"])
        break
'
}

get_active() {
	local out
	out=$(query_active)
	[ -n "$out" ] || return 1
	ACTIVE_ID=${out%% *}
	ACTIVE_REM=${out#* }
}

ask_reason() {
	local prompt="$1" reason
	if ! reason=$(rofi -dmenu -p "$prompt" -lines 0); then
		return 1
	fi
	case "$reason" in
	"" | *[![:space:]]*) ;;
	*) return 1 ;;
	esac
	[ -n "$reason" ] || return 1
	printf '%s' "$reason"
}

parse_secs() {
	python3 - "$1" <<'PYEOF'
import re
import sys

raw = sys.argv[1].strip().lower()
if raw.startswith("+"):
    raw = raw[1:]

if raw.isdigit():
    print(int(raw) * 60)
    sys.exit(0)

match = re.fullmatch(r"(\d+)\s*(h|hr|hrs|m|min|mins|s|sec|secs)", raw)
if not match:
    sys.exit(1)

value, unit = match.groups()
value = int(value)
if unit.startswith("h"):
    value *= 3600
elif unit.startswith("m"):
    value *= 60
print(value)
PYEOF
}

daemon_ok() {
	python3 -c '
import json, sys
try:
    print("1" if json.load(sys.stdin).get("ok") else "0")
except Exception:
    print("0")
'
}

schedule() {
	local secs="$1" response ok
	if get_active; then
		notify "Shutdown already pending" "Use ,off add 5m or ,off cancel."
		return 1
	fi
	response=$("$DAEMON" start "$secs" "Shutdown" --action poweroff)
	ok=$(printf '%s' "$response" | daemon_ok)
	if [ "$ok" != "1" ]; then
		notify "Could not schedule shutdown" "$response"
		return 1
	fi
	notify "Shutdown in $(fmt "$secs")" "Run ,off cancel or ,off add 5m."
}

cancel() {
	local reason response ok
	if ! get_active; then
		notify "No shutdown pending" "Nothing to cancel."
		return 0
	fi
	if ! reason=$(ask_reason "Why cancel shutdown? ($(fmt "$ACTIVE_REM") left)"); then
		return 0
	fi
	response=$("$DAEMON" stop "$ACTIVE_ID" "$reason")
	ok=$(printf '%s' "$response" | daemon_ok)
	if [ "$ok" = "1" ]; then
		notify "Shutdown cancelled" "Reason logged."
	else
		notify "Could not cancel shutdown" "$response"
	fi
}

extend() {
	local secs="$1" reason response ok remaining
	if ! get_active; then
		notify "No shutdown pending" "Start one with ,off."
		return 0
	fi
	if ! reason=$(ask_reason "Why add $(fmt "$secs")?"); then
		return 0
	fi
	response=$("$DAEMON" extend "$ACTIVE_ID" "$secs" "$reason")
	ok=$(printf '%s' "$response" | daemon_ok)
	remaining=$(printf '%s' "$response" | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin).get("remaining", ""))
except Exception:
    pass
')
	if [ "$ok" = "1" ]; then
		notify "Shutdown extended" "$(fmt "${remaining:-0}") left. Reason logged."
	else
		notify "Could not extend shutdown" "$response"
	fi
}

shutdown_now() {
	local choice
	choice=$(printf 'Cancel\nShut down now\n' | rofi -dmenu -p "Power off now?" -no-custom)
	[ "$choice" = "Shut down now" ] || return 0
	if get_active; then
		"$DAEMON" stop "$ACTIVE_ID" "shut down now" >/dev/null
	fi
	notify "Shutting down now" "Poweroff requested."
	sleep 1
	if ! systemctl poweroff; then
		notify "Poweroff failed" "systemctl poweroff returned an error."
	fi
}

add_menu() {
	local choice
	if ! get_active; then
		notify "No shutdown pending" "Start one with ,off."
		return 0
	fi
	choice=$(printf 'Add 5 minutes\nAdd 15 minutes\n' | rofi -dmenu -p "Extend shutdown" -no-custom)
	case "$choice" in
	"Add 5 minutes") extend "$ADD_SECS" ;;
	"Add 15 minutes") extend "$ADD_LONG_SECS" ;;
	esac
}

status() {
	if get_active; then
		printf 'Shutdown in %s\n' "$(fmt "$ACTIVE_REM")"
	else
		printf 'No shutdown pending\n'
	fi
}

menu() {
	local choice
	if get_active; then
		choice=$(printf 'Add 5 minutes\nAdd 15 minutes\nCancel shutdown\nShut down now\n' |
			rofi -dmenu -i -p "Shutdown in $(fmt "$ACTIVE_REM")" -no-custom)
		case "$choice" in
		"Add 5 minutes") extend "$ADD_SECS" ;;
		"Add 15 minutes") extend "$ADD_LONG_SECS" ;;
		"Cancel shutdown") cancel ;;
		"Shut down now") shutdown_now ;;
		esac
	else
		choice=$(printf 'Shut down in 60 seconds\nShut down in 5 minutes\nShut down in 15 minutes\nShut down now\n' |
			rofi -dmenu -i -p "Shutdown" -no-custom)
		case "$choice" in
		"Shut down in 60 seconds") schedule "$DEFAULT_SECS" ;;
		"Shut down in 5 minutes") schedule "$ADD_SECS" ;;
		"Shut down in 15 minutes") schedule "$ADD_LONG_SECS" ;;
		"Shut down now") shutdown_now ;;
		esac
	fi
}

case "${1:-menu}" in
menu) menu ;;
status) status ;;
cancel) cancel ;;
add)
	if [ $# -ge 2 ]; then
		secs=$(parse_secs "$2") || {
			notify "Bad duration" "$2"
			exit 1
		}
		extend "$secs"
	else
		add_menu
	fi
	;;
now) shutdown_now ;;
*)
	secs=$(parse_secs "$1") || {
		notify "Bad duration" "$1"
		exit 1
	}
	schedule "$secs"
	;;
esac
