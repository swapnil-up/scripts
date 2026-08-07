#!/bin/bash
# gopro-ingest.sh
#
# Copies GoPro footage (DCIM/*.MP4) from an SD card to ~/vedit/raw/, renaming
# files with their capture timestamps so names are unique & sortable.
#
# Two ways to run:
#   1. Manually after plugging the card in:
#        gopro-ingest.sh <SD_MOUNT_POINT>
#   2. Automatically via udev (see 99-gopro.rules in this dir). The udev rule
#      runs this script asynchronously with the device node (e.g. sdb1).
#
# Idempotent: already-imported files are skipped (by name), so re-running is safe.
set -euo pipefail

RAW_DIR="${VEDIT_RAW:-$HOME/vedit/raw}"
LOG="$HOME/vedit/ingest.log"

log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; echo "$*"; }

# --- resolve the mount point from either a device node (/dev/sdX1) or a path ---
resolve_mountpoint() {
    local arg="$1"
    if [[ "$arg" = /dev/* ]]; then
        udevadm settle --timeout=5 2>/dev/null || true
        # Wait briefly for the mount to appear.
        for _ in {1..20}; do
            local mp
            mp=$(lsblk -no MOUNTPOINT "$arg" 2>/dev/null)
            if [[ -n "$mp" ]] && [[ "$mp" != " " ]]; then
                echo "$mp"
                return 0
            fi
            sleep 0.3
        done
        return 1
    fi
    echo "$arg"
}

# --- find the GoPro DCIM directory (also handles generic camera) ---
find_dcim() {
    local base="$1"
    for candidate in "$base/DCIM" "$base/dcim"; do
        if [[ -d "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done
    # fall back to looking for any *.MP4 recursively (some cards mount DCIM differently)
    local f
    f=$(find "$base" -maxdepth 3 -type f \( -iname '*.MP4' -o -iname '*.MOV' \) 2>/dev/null | head -n 1)
    if [[ -n "$f" ]]; then
        echo "$(dirname "$f")"
        return 0
    fi
    return 1
}

# --- extract a capture timestamp from a GOPRO file; fall back to file mtime ---
capture_ts() {
    local file="$1"
    if command -v ffprobe >/dev/null 2>&1; then
        local tag
        tag=$(ffprobe -v error -show_entries format_tags=creation_time -of default=nk=1:nw=1 "$file" 2>/dev/null | head -n1)
        if [[ "$tag" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2} ]]; then
            echo "${tag:0:10} ${tag:11:8}" | tr ' ' '_' | tr -d ':'   # YYYYMMDD_HHMMSS
            return 0
        fi
    fi
    date -r "$file" +%Y%m%d_%H%M%S 2>/dev/null || echo "unknown"
}

safe_name() {
    # sanitize the original GoPro name and prepend its timestamp
    local base="$1"
    local ts="$2"
    local clean
    clean=$(basename "$base" | tr ' ' '_' | tr -cd '[:alnum:]_.-')
    printf '%s_%s' "$ts" "$clean"
}

main() {
    mkdir -p "$RAW_DIR"
    local mountpoint
    mountpoint=$(resolve_mountpoint "$1") || { log "Could not find mountpoint for $1"; exit 1; }
    log "Scanning $mountpoint for GoPro footage..."

    local dcim
    dcim=$(find_dcim "$mountpoint")
    if [[ -z "$dcim" ]]; then
        log "No DCIM/media found on $mountpoint."
        exit 0
    fi

    local copied=0 skipped=0
    while IFS= read -r f; do
        [[ -n "$f" ]] || continue
        ts=$(capture_ts "$f")
        name=$(safe_name "$f" "$ts")
        dest="$RAW_DIR/$name"
        if [[ -f "$dest" ]]; then
            skipped=$((skipped + 1))
            log "skip $name"
        else
            cp -n "$f" "$dest"
            copied=$((copied + 1))
            log "import $name <- $f"
        fi
    done < <(find "$dcim" -maxdepth 3 -type f \( -iname '*.MP4' -o -iname '*.MOV' \) 2>/dev/null)

    log "Done: $copied imported, $skipped skipped from $mountpoint."
}

main "$@"