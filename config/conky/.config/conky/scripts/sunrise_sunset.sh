#!/bin/bash

LAT="27.7"
LNG="85.3"
TZ_OFFSET=20700

DATA=$(curl -s "https://api.sunrise-sunset.org/json?lat=$LAT&lng=$LNG")

if echo "$DATA" | jq -e '.status == "OK"' > /dev/null 2>&1; then
	SUNRISE=$(echo "$DATA" | jq -r '.results.sunrise')
	SUNSET=$(echo "$DATA" | jq -r '.results.sunset')
	DAY_LENGTH=$(echo "$DATA" | jq -r '.results.day_length')

	convert_to_local() {
		local time_str="$1"
		local hours=$(echo "$time_str" | cut -d: -f1)
		local mins=$(echo "$time_str" | cut -d: -f2)
		local secs=$(echo "$time_str" | cut -d: -f3 | cut -d' ' -f1)
		local period=$(echo "$time_str" | grep -o '[AP]M')

		hours=$((10#$hours))
		if [ "$period" = "PM" ] && [ "$hours" -ne 12 ]; then
			hours=$((hours + 12))
		elif [ "$period" = "AM" ] && [ "$hours" -eq 12 ]; then
			hours=0
		fi

		local total_secs=$((hours * 3600 + 10#$mins * 60 + 10#$secs + TZ_OFFSET))
		local new_hours=$(( (total_secs / 3600) % 24 ))
		local remainder=$((total_secs % 3600))
		local new_mins=$((remainder / 60))

		printf "%02d:%02d" "$new_hours" "$new_mins"
	}

	SUNRISE_LOCAL=$(convert_to_local "$SUNRISE")
	SUNSET_LOCAL=$(convert_to_local "$SUNSET")

	echo "rise $SUNRISE_LOCAL"
	echo "set $SUNSET_LOCAL"
	echo "len $DAY_LENGTH"
else
	echo "rise --:--"
	echo "set --:--"
	echo "len --:--:--"
fi
