#!/bin/bash
source "$(dirname "$0")/whisper-lib.sh"

TEMP_AUDIO="/tmp/whisper_audio.wav"

export DISPLAY=${DISPLAY:-:0}

rm -f "$TEMP_AUDIO"
trap 'rm -f "$TEMP_AUDIO"; exit' USR1

notify-send "Whisper" "Listening... (Press 'ctrl+c' to stop)" -i audio-input-microphone

parecord --format=s16le --rate=16000 --channels=1 "$TEMP_AUDIO" 2>/dev/null

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
