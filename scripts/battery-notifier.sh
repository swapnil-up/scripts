#!/bin/bash
set -euo pipefail

LOW_BATTERY_LEVEL=30
HIGH_BATTERY_LEVEL=100

BATTERY_PATH=$(compgen -G /sys/class/power_supply/BAT* | head -1)
if [ -z "$BATTERY_PATH" ]; then
	exit 0
fi

while true; do
	BATTERY_PERCENT=$(cat "$BATTERY_PATH/capacity")
	STATUS=$(cat "$BATTERY_PATH/status")

	# Notify if battery is low
	if [ "$BATTERY_PERCENT" -le "$LOW_BATTERY_LEVEL" ] && [ "$STATUS" != "Charging" ]; then
		notify-send "Low Battery" "Battery at $BATTERY_PERCENT%. Please charge!" -u critical
	fi

	# Notify if battery is full
	if [ "$BATTERY_PERCENT" -ge "$HIGH_BATTERY_LEVEL" ] && [ "$STATUS" = "Charging" ]; then
		notify-send "Battery Full" "Battery is fully charged. Please unplug the charger." -u normal
	fi

	# Wait before checking again
	sleep 60
done
