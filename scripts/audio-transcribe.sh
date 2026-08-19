#!/bin/bash
set -uo pipefail

source "$(dirname "$0")/utils/whisper-lib.sh"

die() {
    notify-send "Audio Transcribe" "$1" -i dialog-error 2>/dev/null || true
    echo "ERROR: $1" >&2
    read -rsp "Press Enter to exit..." >&2
    exit 1
}

if [ -z "${GEMINI_API_KEY:-}" ]; then
    ENVFILE="$(dirname "$0")/../.env"
    [ -f "$ENVFILE" ] && source "$ENVFILE"
fi

[ -z "${GEMINI_API_KEY:-}" ] && die "GEMINI_API_KEY not set. Add it to scripts/.env"

# ── pick file ─────────────────────────────────────────────────────
if [ "${1:-}" != "" ]; then
    INPUT="$1"
else
    AUDIO_FILES=$(find "$HOME" -maxdepth 5 -type f \
        \( -iname '*.mp3' -o -iname '*.wav' -o -iname '*.m4a' \
           -o -iname '*.aac' -o -iname '*.ogg' -o -iname '*.flac' \
           -o -iname '*.opus' -o -iname '*.wma' -o -iname '*.ape' \
           -o -iname '*.alac' -o -iname '*.aiff' -o -iname '*.mid' \
           -o -iname '*.midi' -o -iname '*.webm' -o -iname '*.mp4' \
           -o -iname '*.mkv' -o -iname '*.avi' -o -iname '*.mov' \
           -o -iname '*.weba' -o -iname '*.spx' -o -iname '*.ac3' \
           -o -iname '*.dts' -o -iname '*.mka' -o -iname '*.tta' \
           -o -iname '*.tak' -o -iname '*.dsf' -o -iname '*.dff' \
           -o -iname '*.caf' -o -iname '*.wv' \) 2>/dev/null || true)

    [ -z "$AUDIO_FILES" ] && die "No audio files found"

    sleep 0.3
    INPUT=$(echo "$AUDIO_FILES" | fzf --prompt="Audio > " --height 40% --reverse) || true
    [ -z "$INPUT" ] && { echo "Cancelled."; exit 0; }
fi

[ -f "$INPUT" ] || die "File not found: $INPUT"

BASENAME="${INPUT##*/}"
NAME="${BASENAME%.*}"
DIR="$(dirname "$INPUT")"
OUTPUT="$DIR/${NAME}_cleaned.txt"
TMPRAW=$(mktemp /tmp/raw_transcript_XXXXXX.txt)
TMPWAV=""
trap 'rm -f "$TMPRAW" "$TMPWAV"' EXIT

# whisper needs 16kHz mono wav — convert if needed
EXT="${INPUT##*.}"
if [ "${EXT,,}" != "wav" ]; then
    TMPWAV=$(mktemp /tmp/whisper_input_XXXXXX.wav)
    ffmpeg -y -i "$INPUT" -ar 16000 -ac 1 -c:a pcm_s16le "$TMPWAV" 2>/dev/null || die "ffmpeg conversion failed"
    INPUT="$TMPWAV"
fi

# ── transcribe ────────────────────────────────────────────────────
echo "Transcribing: $INPUT"
RAW=$(transcribe "$INPUT") || die "Whisper transcription failed"
[ -z "$RAW" ] && die "Transcription was empty"
echo "$RAW" > "$TMPRAW"

echo "Raw transcript (${#RAW} chars). Cleaning with Gemini..."

# ── clean with gemini ─────────────────────────────────────────────
CLEANED=$(python3 - "$GEMINI_API_KEY" "$TMPRAW" <<'PYEOF'
import json, sys, urllib.request

api_key = sys.argv[1]
with open(sys.argv[2]) as f:
    raw = f.read()

prompt = (
    "You are an editor cleaning up an audio transcript produced by Whisper. "
    "Fix grammar, punctuation, and spelling. Correct words Whisper likely "
    "mistranscribed (listen for context clues). Preserve the original meaning "
    "and structure — do not add content or reorder paragraphs. Remove filler "
    "words (um, uh, like, you know) unless they carry meaning. Return ONLY "
    "the cleaned text, no commentary."
)

body = json.dumps({
    "contents": [{"parts": [{"text": prompt}, {"text": raw}]}],
    "generationConfig": {"temperature": 0.2}
}).encode()

req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}",
    data=body,
    headers={"Content-Type": "application/json"},
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        r = json.loads(resp.read())
    text = r["candidates"][0]["content"]["parts"][0]["text"]
    print(text, end="")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
) || die "Gemini API call failed"

[ -z "$CLEANED" ] && die "Gemini returned empty response"

# ── save + copy ───────────────────────────────────────────────────
echo "$CLEANED" > "$OUTPUT"
echo "$CLEANED" | xclip -selection clipboard

notify-send "Audio Transcribe" "Saved: $OUTPUT\nCopied to clipboard" -i edit-paste 2>/dev/null || true
echo "Done → $OUTPUT"
