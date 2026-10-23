#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=versions.env
source "$SCRIPT_DIR/versions.env"

echo ">>> PYTHON_START <<<"
echo "--- Installing Python dependencies ---"

WITH_OPTIONAL=false
if [ "${1:-}" = "--optional" ] || [ "${INSTALL_OPTIONAL:-0}" = "1" ]; then
	WITH_OPTIONAL=true
fi

if ! command -v pyenv >/dev/null 2>&1; then
	echo "ERROR: pyenv is not installed; run languages.sh first" >&2
	exit 1
fi

echo "Ensuring Python $PYTHON_VERSION is installed..."
pyenv install -s "$PYTHON_VERSION"
pyenv global "$PYTHON_VERSION"
pyenv rehash

PYTHON_BIN="$HOME/.pyenv/versions/$PYTHON_VERSION/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
	echo "ERROR: Python interpreter not found at $PYTHON_BIN" >&2
	exit 1
fi

echo "Installing base requirements..."
"$PYTHON_BIN" -m pip install --quiet --upgrade pip
"$PYTHON_BIN" -m pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

if $WITH_OPTIONAL; then
	echo "Installing optional requirements (chromadb, numpy, playwright)..."
	"$PYTHON_BIN" -m pip install --quiet -r "$SCRIPT_DIR/requirements-optional.txt"
	echo "Installing Playwright Chromium..."
	"$PYTHON_BIN" -m playwright install chromium
else
	echo "Skipping optional Python dependencies (use --optional)."
fi

echo "Python: $("$PYTHON_BIN" --version 2>&1)"
echo ">>> PYTHON_COMPLETE <<<"
