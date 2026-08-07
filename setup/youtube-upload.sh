#!/bin/bash
set -euo pipefail

echo ">>> YOUTUBE_UPLOAD_START <<<"
echo "--- Installing youtubeuploader (YouTube uploads for vedit) ---"
# Local YouTube CLI uploads used by scripts/editor/upload.py.
# Uses the prebuilt release binary (no Go toolchain needed). Idempotent:
# rerunning upgrades an existing install and skips what's already configured.

BIN_DIR="$HOME/opt/youtubeuploader"
BIN_PATH="$BIN_DIR/youtubeuploader"
CONF_DIR="$HOME/.config/youtubeuploader"
SECRETS_PATH="$CONF_DIR/client_secrets.json"
CANDIDATE="$HOME/Downloads/client_secret_*.apps.googleusercontent.com.json"

mkdir -p "$BIN_DIR" "$CONF_DIR"

# 1. Install/refresh the binary from the latest GitHub release
#    (Linux behaves as amd64 on x86_64; fall back to arm64 on Raspberry Pi-type hosts)
case "$(uname -m)" in
x86_64) REL_ASSET="Linux_amd64" ;;
aarch64|arm64) REL_ASSET="Linux_arm64" ;;
*) echo "ERROR: unsupported arch: $(uname -m)"; exit 1 ;;
esac

if [ -x "$BIN_PATH" ] && "$BIN_PATH" -h >/dev/null 2>&1; then
	echo "youtubeuploader already installed — skipping binary download."
else
	TMP="$(mktemp -d)"
	trap 'rm -rf "$TMP"' EXIT
	echo "Downloading youtubeuploader ($REL_ASSET)..."
	# Resolve the current release version, then build the exact asset URL
	# (GitHub's /latest/download/ only redirects exact, versioned filenames).
	VER="$(curl -sL https://api.github.com/repos/porjo/youtubeuploader/releases/latest | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p')"
	if [ -z "$VER" ]; then
		echo "ERROR: could not resolve latest youtubeuploader release."
		exit 1
	fi
	URL="https://github.com/porjo/youtubeuploader/releases/download/${VER}/youtubeuploader_${VER#v}_${REL_ASSET}.tar.gz"
	curl -fSL "$URL" -o "$TMP/yt.tar.gz"
	tar xzf "$TMP/yt.tar.gz" -C "$TMP"
	BIN_FILE="$(find "$TMP" -maxdepth 1 -type f -name youtubeuploader -executable | head -n1)"
	if [ -z "$BIN_FILE" ]; then
		echo "ERROR: Archive did not contain a youtubeuploader binary."
		exit 1
	fi
	chmod +x "$BIN_FILE"
	cp "$BIN_FILE" "$BIN_PATH"
	echo "Installed youtubeuploader to $BIN_PATH"
fi

# 2. Install client_secrets.json if present from a Google Cloud OAuth download
#    (skipped if one is already configured; you choose which device's secret wins).
if [ -f "$SECRETS_PATH" ]; then
	echo "client_secrets.json already present, keeping it."
elif compgen -G "$CANDIDATE" >/dev/null; then
	SRC="$(ls -t $CANDIDATE 2>/dev/null | head -n1)"
	cp "$SRC" "$SECRETS_PATH"
	chmod 600 "$SECRETS_PATH"
	echo "Installed client_secrets.json from $SRC"
else
	echo "NOTE: no client_secrets.json found. Download one from Google Cloud Console:"
	echo "  APIs & Services > Library > YouTube Data API v3 > Enable"
	echo "  Credentials > Create OAuth client ID > Desktop app > Download JSON"
	echo "  place it at $SECRETS_PATH"
fi

# 3. OAuth token — cannot be provisioned headless; it's created on the first
#    real upload (opens a browser). Just report state.
if [ -f "$CONF_DIR/request.token" ]; then
	echo "OAuth token already cached ($CONF_DIR/request.token)."
else
	echo "NOTE: no OAuth token yet. It is created automatically on first upload"
	echo "      (run upload.py; a browser will open once for authorization)."
fi

echo "Verify with:  ~/opt/youtubeuploader/youtubeuploader -h"
echo ">>> YOUTUBE_UPLOAD_COMPLETE <<<"