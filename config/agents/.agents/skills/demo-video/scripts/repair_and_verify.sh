#!/usr/bin/env bash
# Repair a Playwright recording's scrambled timeline and verify it.
#
#   usage: repair_and_verify.sh <raw.webm> <out.mp4> [fps]
#
# Playwright writes frames in the correct order but with non-monotonic
# timestamps, and any naive ffmpeg transcode reorders by them. setpts=N/fps/TB
# turns storage order into the timeline; bframes=0 stops libx264 reordering.
set -euo pipefail

RAW="${1:?usage: repair_and_verify.sh <raw.webm> <out.mp4> [fps]}"
OUT="${2:?usage: repair_and_verify.sh <raw.webm> <out.mp4> [fps]}"
FPS="${3:-25}"

echo ">> encoding $OUT (setpts=N/${FPS}/TB, bframes=0)"
ffmpeg -y -v error -i "$RAW" \
  -vf "setpts=N/${FPS}/TB" \
  -c:v libx264 -x264-params bframes=0 -preset medium -crf 20 \
  -pix_fmt yuv420p -movflags +faststart -an "$OUT"

echo ">> output stream"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,nb_frames,avg_frame_rate \
  -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT"

SHEET="${OUT%.*}-sheet.png"
echo ">> contact sheet -> $SHEET (tile k = second k, 6 per row)"
ffmpeg -y -v error -i "$OUT" -vf "fps=1,scale=240:-1,tile=6x12" -frames:v 1 "$SHEET"

cat <<EOF

>> MANUAL CHECK (index and seek must agree, and match the wall clock):
   ffmpeg -ss 30 -i "$OUT" -frames:v 1 /tmp/t30.png
   ffmpeg -i "$OUT" -vf "select='eq(n\\,750)'" -vsync 0 -frames:v 1 /tmp/n750.png
   Open $SHEET and scan the sequence against your session log.

   Reminder: -ss BEFORE -i is unreliable on these files, and md5 across codecs
   is meaningless (VP8 vs H.264 pixels differ) — compare content visually.
EOF
