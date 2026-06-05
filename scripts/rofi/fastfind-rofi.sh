#!/bin/bash
# fastfind-rofi.sh — Search files under ~/github via rofi + fastfind.
#   Press $mod+g in i3 to activate.

FASTFIND_BIN="$HOME/github/search/fastfind-release"
PATHS_FILE="$HOME/.cache/fastfind/paths.txt"
DATASET_DIR="$HOME/github"
SOCKET_PATH="/tmp/fastfind.sock"

mkdir -p "$HOME/.cache/fastfind"

# ── ensure paths file exists ──────────────────────────────────────
if [ ! -f "$PATHS_FILE" ]; then
    notify-send "fastfind" "Building file index from $DATASET_DIR …"
    find "$DATASET_DIR" -type f \
        -not -path '*/node_modules/*' \
        -not -path '*/.git/*' \
        -not -path '*/target/*' \
        -not -path '*/venv/*' \
        -not -path '*/__pycache__/*' \
        > "$PATHS_FILE"
fi

# ── start daemon if not running ──────────────────────────────────
if [ ! -S "$SOCKET_PATH" ]; then
    if [ ! -x "$FASTFIND_BIN" ]; then
        notify-send -u critical "fastfind" "Binary not found — run 'make release' in ~/github/search"
        exit 1
    fi
    "$FASTFIND_BIN" daemon "$PATHS_FILE" &
    for _ in $(seq 1 30); do
        if [ -S "$SOCKET_PATH" ]; then break; fi
        sleep 0.05
    done
    if [ ! -S "$SOCKET_PATH" ]; then
        notify-send -u critical "fastfind" "Daemon failed to start"; exit 1
    fi
fi

# ── get query ────────────────────────────────────────────────────
# Send empty string so rofi shows a blank list.  User types + Enter.
QUERY=$(echo "" | rofi -dmenu -i -p "File search")
if [ -z "$QUERY" ]; then
    exit 0
fi

# ── search via daemon ────────────────────────────────────────────
RESULTS=$("$FASTFIND_BIN" query "$QUERY" 2>/dev/null)
COUNT=$(echo "$RESULTS" | head -1 | tr -d '[:space:]')

if [ -z "$COUNT" ] || [ "$COUNT" = "0" ]; then
    notify-send "fastfind" "No results for: $QUERY"
    exit 0
fi

# ── show results for selection ───────────────────────────────────
SELECTED=$(echo "$RESULTS" | tail -n +2 | rofi -dmenu -i -p "Results ($COUNT)")
if [ -n "$SELECTED" ]; then
    xdg-open "$SELECTED"
fi
