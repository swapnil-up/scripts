#!/bin/bash
# gopro-organize.sh
#
# Organizes GoPro files from a flat directory into:
#   photos/YYYY-MM-DD/YYYY-MM-DD_HHMMSS_goproNNNN.JPG
#   video/YYYY-MM-DD/YYYY-MM-DD_HHMMSS_goproNNNN.MP4
#
# Removes .THM thumbnails. Extracts capture timestamps via ffprobe (video)
# or EXIF via Python/PIL (photo). Falls back to file mtime.
#
# Usage:
#   gopro-organize.sh [SOURCE_DIR]
#
# SOURCE_DIR defaults to ~/clicks/gopro. Files are moved (not copied).
set -euo pipefail

SRC="${1:-$HOME/clicks/gopro}"

log() { echo "$*"; }

die() { echo "error: $*" >&2; exit 1; }

[[ -d "$SRC" ]] || die "source directory not found: $SRC"

# --- extract timestamp from video via ffprobe ---
video_ts() {
    local file="$1"
    if command -v ffprobe >/dev/null 2>&1; then
        local tag
        tag=$(ffprobe -v error -show_entries format_tags=creation_time \
              -of default=nk=1:nw=1 "$file" 2>/dev/null | head -n1)
        if [[ "$tag" =~ ^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2}) ]]; then
            echo "${BASH_REMATCH[1]}-${BASH_REMATCH[2]}-${BASH_REMATCH[3]}_${BASH_REMATCH[4]}${BASH_REMATCH[5]}${BASH_REMATCH[6]}"
            return 0
        fi
    fi
    date -r "$file" +%Y-%m-%d_%H%M%S 2>/dev/null || echo "unknown_unknown"
}

# --- extract timestamp from photo via Python/PIL ---
photo_ts() {
    local file="$1"
    python3 -c "
from PIL import Image
from PIL.ExifTags import TAGS
try:
    img = Image.open('$file')
    exif = img._getexif()
    if exif:
        dt = None
        for k, v in exif.items():
            tag = TAGS.get(k, k)
            if tag == 'DateTimeOriginal':
                dt = v
                break
        if dt:
            # '2024:06:17 10:55:42' -> '2024-06-17_105542'
            print(dt.replace(':', '-', 2).replace(' ', '_').replace(':', ''))
except Exception:
    pass
" 2>/dev/null
}

# --- sanitize a context word from the original GoPro filename ---
context_from_name() {
    local basename="$1"
    # GOPR4746 -> gopro4746, GX014735 -> gopro014735
    echo "$basename" | sed -E 's/^[A-Z]+/gopro/' | tr '[:upper:]' '[:lower:]'
}

# --- main ---
declare -i moved=0 skipped=0

# Phase 1: delete thumbnails
while IFS= read -r -d '' thm; do
    rm -f "$thm"
    log "deleted $(basename "$thm")"
done < <(find "$SRC" -maxdepth 1 -type f -iname '*.THM' -print0 2>/dev/null)

# Phase 2: process photos (JPG/JPEG)
while IFS= read -r -d '' f; do
    [[ -n "$f" ]] || continue
    bn=$(basename "$f")
    ext="${bn##*.}"
    stem="${bn%.*}"
    ts=$(photo_ts "$f")
    [[ -z "$ts" || "$ts" == "unknown_unknown" ]] && ts=$(date -r "$f" +%Y-%m-%d_%H%M%S 2>/dev/null || echo "unknown_unknown")
    date_part="${ts%%_*}"
    ctx=$(context_from_name "$stem")
    newname="${ts}_${ctx}.${ext,,}"
    dest_dir="$SRC/photos/$date_part"
    mkdir -p "$dest_dir"
    dest="$dest_dir/$newname"
    if [[ -f "$dest" ]]; then
        skipped=$((skipped + 1))
        log "skip $bn (already exists as $newname)"
    else
        mv "$f" "$dest"
        moved=$((moved + 1))
        log "photo $bn -> $newname"
    fi
done < <(find "$SRC" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) -print0 2>/dev/null)

# Phase 3: process videos (MP4/MOV)
while IFS= read -r -d '' f; do
    [[ -n "$f" ]] || continue
    bn=$(basename "$f")
    ext="${bn##*.}"
    stem="${bn%.*}"
    ts=$(video_ts "$f")
    [[ -z "$ts" || "$ts" == "unknown_unknown" ]] && ts=$(date -r "$f" +%Y-%m-%d_%H%M%S 2>/dev/null || echo "unknown_unknown")
    date_part="${ts%%_*}"
    ctx=$(context_from_name "$stem")
    newname="${ts}_${ctx}.${ext}"
    dest_dir="$SRC/video/$date_part"
    mkdir -p "$dest_dir"
    dest="$dest_dir/$newname"
    if [[ -f "$dest" ]]; then
        skipped=$((skipped + 1))
        log "skip $bn (already exists as $newname)"
    else
        mv "$f" "$dest"
        moved=$((moved + 1))
        log "video $bn -> $newname"
    fi
done < <(find "$SRC" -maxdepth 1 -type f \( -iname '*.mp4' -o -iname '*.mov' \) -print0 2>/dev/null)

echo ""
echo "Done: $moved files organized, $skipped skipped."
echo ""
echo "Structure:"
find "$SRC/photos" "$SRC/video" -type f 2>/dev/null | sort | while read -r line; do
    echo "  ${line#"$SRC/"}"
done
