#!/bin/bash
set -euo pipefail

CPU_THRESHOLD=90
MEMORY_THRESHOLD=90

while true; do
	PREV_IDLE=$(awk '/^cpu / {print $5}' /proc/stat)
	PREV_TOTAL=$(awk '/^cpu / {sum=$2+$3+$4+$5+$6+$7+$8+$9+$10+$11; print sum}' /proc/stat)
	sleep 1
	CURR_IDLE=$(awk '/^cpu / {print $5}' /proc/stat)
	CURR_TOTAL=$(awk '/^cpu / {sum=$2+$3+$4+$5+$6+$7+$8+$9+$10+$11; print sum}' /proc/stat)
	CPU_USAGE=$((100 * (CURR_TOTAL - PREV_TOTAL - (CURR_IDLE - PREV_IDLE)) / (CURR_TOTAL - PREV_TOTAL)))

	# Get Memory usage
	MEM_TOTAL=$(grep MemTotal /proc/meminfo | awk '{print $2}')
	MEM_AVAILABLE=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
	MEM_USAGE=$(((MEM_TOTAL - MEM_AVAILABLE) * 100 / MEM_TOTAL))

	# Notify if CPU usage exceeds threshold
	if ((${CPU_USAGE%.*} > CPU_THRESHOLD)); then
		notify-send "High CPU Usage" "CPU usage is at ${CPU_USAGE}%!"
	fi

	# Notify if Memory usage exceeds threshold
	if ((MEM_USAGE > MEMORY_THRESHOLD)); then
		notify-send "High Memory Usage" "Memory usage is at ${MEM_USAGE}%!"
	fi

	# Wait before checking again (adjust as needed)
	sleep 30
done
