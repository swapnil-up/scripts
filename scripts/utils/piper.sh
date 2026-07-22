#!/bin/bash

# --- CONFIGURATION ---
PIPER_DIR="$HOME/github/piper_tts-1.4.2"
MODEL_PATH="$PIPER_DIR/en_US-lessac-medium.onnx"
DEFAULT_SPEED="0.7"

export PATH="$PIPER_DIR:$PATH"
export LD_LIBRARY_PATH="$PIPER_DIR:$LD_LIBRARY_PATH"

if pgrep -x "piper" >/dev/null; then
	pkill piper && pkill aplay
	notify-send "Piper TTS" "Stopped reading."
	exit 0
fi

SPEED=${1:-$DEFAULT_SPEED}

# Get text from clipboard
TEXT=$(xclip -selection clipboard -o)

if [ -z "$TEXT" ]; then
	notify-send "Piper TTS" "Clipboard is empty!" -u low
	exit 1
fi

# Pre-process: join broken lines from PDFs (single newline -> space), keep paragraph breaks
TEXT=$(printf '%s' "$TEXT" | awk 'NF { printf "%s%s", (NR>1 ? " " : ""), $0; next } { printf "\n\n" }')

notify-send "Piper TTS" "Reading clipboard..." -i audio-speakers

printf '%s' "$TEXT" | piper --model $MODEL_PATH --length_scale $SPEED --output_raw | aplay -r 22050 -f S16_LE -t raw
xclip -selection clipboard -o >/dev/null 2>&1
