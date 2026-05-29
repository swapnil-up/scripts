#!/bin/bash
source "$(dirname "$0")/whisper-lib.sh"

TEMP_AUDIO="/tmp/whisper_audio.wav"

export DISPLAY=${DISPLAY:-:0}

rm -f "$TEMP_AUDIO"

stop_recording() {
    # Give a 500ms cushion for trailing audio/buffers before killing parecord
    sleep 0.5
    kill "$PARECORD_PID" 2>/dev/null
}
# Trap Ctrl+C (SIGINT) and your USR1 signal to trigger the graceful stop
trap 'stop_recording' INT USR1

notify-send "Whisper" "Listening... (Press 'ctrl+c' to stop)" -i audio-input-microphone

# Run parecord in the background so the script can listen for the trap
parecord --format=s16le --rate=16000 --channels=1 "$TEMP_AUDIO" 2>/dev/null &
PARECORD_PID=$!

# Wait for parecord to finish (which happens after the trap kills it)
wait "$PARECORD_PID" 2>/dev/null

notify-send "Whisper" "Transcribing..." -i software-update-available

CLEAN_TEXT=$(transcribe "$TEMP_AUDIO")

if [ -n "$CLEAN_TEXT" ]; then
    echo "$CLEAN_TEXT" | xclip -selection clipboard
    notify-send "Whisper Copied" "$CLEAN_TEXT" -i edit-paste
else
    echo "Error: Transcription was empty."
    notify-send "Whisper Error" "Transcription was empty"
fi

rm -f "$TEMP_AUDIO"