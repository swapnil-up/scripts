WHISPER_ROOT="$HOME/github/whisper.cpp"
WHISPER_EXE="$WHISPER_ROOT/build/bin/whisper-cli"
MODEL_PATH="$WHISPER_ROOT/models/ggml-base.en.bin"

transcribe() {
    local audio_file="$1"
    if [ ! -f "$audio_file" ] || [ ! -s "$audio_file" ]; then
        return 1
    fi
    TRANSCRIPTION=$($WHISPER_EXE -m "$MODEL_PATH" -f "$audio_file" -nt 2>/dev/null)
    CLEAN_TEXT=$(echo "$TRANSCRIPTION" | sed -e 's/\[.*\]//g' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    echo "$CLEAN_TEXT"
}
