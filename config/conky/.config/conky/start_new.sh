#!/bin/bash
# Start new conky widgets
conky -c ~/.config/conky/conky_sunrise.conf &
conky -c ~/.config/conky/conky_xkcd.conf &
echo "Sunrise and XKCD widgets started"
