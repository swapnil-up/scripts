#!/bin/bash
set -uo pipefail

BATTERY_PATH=$(compgen -G /sys/class/power_supply/BAT* | head -1) || true
if [ -z "$BATTERY_PATH" ]; then
	exit 0
fi

# Thresholds to warn at, in descending order
THRESHOLDS=(30 20 15 10 5)
notified=""

notify_at() {
	local pct=$1
	# Only notify if we haven't already at this threshold
	case " $notified " in
		*" $pct "*) return ;;
	esac
	notify-send "Low Battery" "Battery at $pct%. Please charge!" -u critical
	notified="$notified $pct"
}

notified_full=false

while true; do
	BATTERY_PERCENT=$(cat "$BATTERY_PATH/capacity")
	STATUS=$(cat "$BATTERY_PATH/status")

	if [ "$STATUS" = "Charging" ]; then
		# Reset low-battery thresholds when plugged in
		notified=""
		# Notify once when reaching full charge
		if [ "$BATTERY_PERCENT" -ge 100 ] && [ "$notified_full" = false ]; then
			notify-send "Battery Full" "Battery is fully charged." -u normal
			notified_full=true
		fi
	else
		notified_full=false
		# Check each threshold
		for thresh in "${THRESHOLDS[@]}"; do
			if [ "$BATTERY_PERCENT" -le "$thresh" ]; then
				notify_at "$thresh"
				break
			fi
		done
	fi

	sleep 60
done
