#!/bin/bash
set -euo pipefail

echo ">>> PIPER_START <<<"
echo "--- Setting up piper TTS ---"

PIPER_VERSION="2023.11.14-2"
PIPER_DIR="$HOME/github/piper_tts-1.4.2"
MODEL_NAME="en_US-lessac-medium"
BIN_URL="https://github.com/rhasspy/piper/releases/download/$PIPER_VERSION/piper_linux_x86_64.tar.gz"
MODEL_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"

mkdir -p "$PIPER_DIR"

# 1. Install piper binary
if [ ! -f "$PIPER_DIR/piper" ]; then
	echo "Downloading piper binary..."
	TMP_TAR=$(mktemp)
	curl -fSL "$BIN_URL" -o "$TMP_TAR"
	tar -xzf "$TMP_TAR" -C "$PIPER_DIR" --strip-components=1 piper/piper
	rm -f "$TMP_TAR"
else
	echo "piper binary already exists, skipping."
fi

# 2. Download voice model + config
if [ ! -f "$PIPER_DIR/$MODEL_NAME.onnx" ]; then
	echo "Downloading $MODEL_NAME voice model..."
	curl -fSL "$MODEL_URL" -o "$PIPER_DIR/$MODEL_NAME.onnx"
else
	echo "$MODEL_NAME.onnx already exists, skipping."
fi
if [ ! -f "$PIPER_DIR/$MODEL_NAME.onnx.json" ]; then
	echo "Downloading $MODEL_NAME voice config..."
	curl -fSL "$MODEL_URL.json" -o "$PIPER_DIR/$MODEL_NAME.onnx.json"
else
	echo "$MODEL_NAME.onnx.json already exists, skipping."
fi

# 3. Ensure in PATH via .bashrc if not already
LINE="export PATH=\"\$PATH:$PIPER_DIR\""
if ! grep -qxF "export PATH=\"\$PATH:$PIPER_DIR\"" "$HOME/.bashrc" 2>/dev/null; then
	echo "Adding piper to PATH in .bashrc..."
	printf "\n# piper TTS\n%s\n" "$LINE" >> "$HOME/.bashrc"
fi

echo "piper TTS ready at $PIPER_DIR"
echo "Run 'source ~/.bashrc' or log out/in for PATH to take effect."
echo ">>> PIPER_COMPLETE <<<"
