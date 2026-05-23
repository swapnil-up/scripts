#!/bin/bash
set -euo pipefail

echo ">>> SOURCE_START <<<"
echo "--- Building from GitHub Source (in ~/github) ---"

mkdir -p "$HOME/github"
# 1. CMake
if ! command -v cmake &>/dev/null; then
	echo "Building CMake (this will take a while, check setup.log for details)..."
	REPO_DIR="$HOME/github/CMake"
	[ ! -d "$REPO_DIR" ] && git clone --depth 1 https://github.com/Kitware/CMake.git "$REPO_DIR" >> "${LOG_FILE:-/dev/null}" 2>&1
	cd "$REPO_DIR"
	git pull >> "${LOG_FILE:-/dev/null}" 2>&1
	./bootstrap --prefix=/usr/local >> "${LOG_FILE:-/dev/null}" 2>&1
	make -j$(nproc) >> "${LOG_FILE:-/dev/null}" 2>&1
	sudo make install >> "${LOG_FILE:-/dev/null}" 2>&1
	cd - >/dev/null
else
	echo "CMake already exists ($(cmake --version | head -n1)), skipping."
fi

# 2. Clipmenu
if ! command -v clipmenu &>/dev/null; then
	echo "Building Clipmenu (check setup.log for details)..."
	REPO_DIR="$HOME/github/clipmenu"
	[ ! -d "$REPO_DIR" ] && git clone https://github.com/cdown/clipmenu.git "$REPO_DIR" >> "${LOG_FILE:-/dev/null}" 2>&1
	cd "$REPO_DIR"
	git pull >> "${LOG_FILE:-/dev/null}" 2>&1
	sudo make install >> "${LOG_FILE:-/dev/null}" 2>&1
	cd - >/dev/null
fi

echo ">>> SOURCE_COMPLETE <<<"
