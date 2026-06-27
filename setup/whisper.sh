#!/bin/bash
set -euo pipefail

echo ">>> WHISPER_START <<<"
echo "--- Building whisper.cpp from source ---"

REPO_DIR="$HOME/github/whisper.cpp"
MODEL_DIR="$REPO_DIR/models"
MODEL_NAME="ggml-small.en.bin"

# 1. Build deps
if ! command -v cmake &>/dev/null; then
	echo "ERROR: cmake is required. Run setup/apt.sh first."
	exit 1
fi

# 2. Clone / pull
if [ ! -d "$REPO_DIR" ]; then
	echo "Cloning whisper.cpp..."
	git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git "$REPO_DIR"
else
	echo "Updating whisper.cpp..."
	git -C "$REPO_DIR" pull --ff-only
fi

# 3. Build (only whisper-cli, not the whole thing)
echo "Building whisper-cli..."
cmake -S "$REPO_DIR" -B "$REPO_DIR/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$REPO_DIR/build" -j"$(nproc)" --target whisper-cli

# 4. Download model
MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$MODEL_NAME"
if [ ! -f "$MODEL_DIR/$MODEL_NAME" ]; then
	echo "Downloading $MODEL_NAME (small English model)..."
	mkdir -p "$MODEL_DIR"
	curl -fSL "$MODEL_URL" -o "$MODEL_DIR/$MODEL_NAME"
else
	echo "$MODEL_NAME already exists, skipping."
fi

echo "whisper.cpp ready at $REPO_DIR"
echo ">>> WHISPER_COMPLETE <<<"
