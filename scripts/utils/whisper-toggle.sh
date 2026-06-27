#!/bin/bash

PID_FILE="/tmp/whisper_toggle.pid"
WHISPER_SCRIPT="$HOME/github/scripts/scripts/utils/whisper.sh"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null; then
    kill -USR1 "$(cat "$PID_FILE")" 2>/dev/null
    rm -f "$PID_FILE"
else
    rm -f "$PID_FILE"
    "$WHISPER_SCRIPT" &
    echo $! > "$PID_FILE"
fi
