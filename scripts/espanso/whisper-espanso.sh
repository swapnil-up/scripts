#!/bin/bash
source "$(dirname "$0")/../utils/whisper-lib.sh"

TEMP_AUDIO="/tmp/whisper_audio_$$.wav"
STOP_FILE="/tmp/whisper_stop_$$"

rm -f "$TEMP_AUDIO" "$STOP_FILE"

notify-send "Whisper" "Recording... (Enter or click to stop)" -i audio-input-microphone

parecord --format=s16le --rate=16000 --channels=1 "$TEMP_AUDIO" 2>/dev/null &
PID=$!

while [ ! -f "$STOP_FILE" ] && kill -0 $PID 2>/dev/null; do
    sleep 0.5
done

kill $PID 2>/dev/null
rm -f "$STOP_FILE"

CLEAN_TEXT=$(transcribe "$TEMP_AUDIO")

if [ -n "$CLEAN_TEXT" ]; then
    printf '%s' "$CLEAN_TEXT"
else
    echo "[empty]"
fi

rm -f "$TEMP_AUDIO"
