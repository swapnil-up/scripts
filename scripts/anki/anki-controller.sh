#!/bin/bash
set -euo pipefail

# Attempt to connect to the Bluetooth device
echo -e "connect FF:FF:40:00:DF:97" | bluetoothctl

# Wait until the device is connected
while true; do
	# Check the connection status
	connected=$(bluetoothctl info FF:FF:40:00:DF:97 | grep "Connected: yes")
	if [ -n "$connected" ]; then
		echo "Device connected!"
		break
	fi
	echo "Waiting for connection..."
	sleep 1
done

# Launch antimicrox
io.github.antimicrox.antimicrox &
