#!/usr/bin/env python3
import sys
import json
import os
from utils import run_ffmpeg, validate_file, format_time


def process_text_overlays(input_file, output_file):
    """
    Apply all text overlays from the .texts.json file
    """
    validate_file(input_file)

    texts_file = f"{input_file}.texts.json"
    if not os.path.exists(texts_file):
        print(f"Error: No text overlays file found ({texts_file})")
        print("Run text_marker.py first to create text overlays")
        sys.exit(1)

    with open(texts_file, "r") as f:
        text_overlays = json.load(f)

    if len(text_overlays) == 0:
        print("No text overlays found.")
        sys.exit(1)

    # Position mapping
    positions = {
        "top": "x=(w-text_w)/2:y=50",
        "center": "x=(w-text_w)/2:y=(h-text_h)/2",
        "bottom": "x=(w-text_w)/2:y=h-th-50",
    }

    # Build complex drawtext filter with all overlays
    drawtext_filters = []

    print(f"Adding {len(text_overlays)} text overlays:")
    for i, overlay in enumerate(text_overlays, 1):
        text = overlay["text"].replace("'", "'\\''")  # Escape single quotes
        start = overlay["start"]
        end = overlay["end"]
        position = positions.get(overlay.get("position", "bottom"), positions["bottom"])
        fontsize = overlay.get("fontsize", 48)
        color = overlay.get("color", "white")

        duration = end - start
        print(f"  {i}. {format_time(start)} ({duration:.1f}s): \"{overlay['text']}\"")

        drawtext = (
            f"drawtext=text='{text}':"
            f"fontsize={fontsize}:"
            f"fontcolor={color}:"
            f"box=1:boxcolor=black@0.5:boxborderw=5:"
            f"{position}:"
            f"enable='between(t,{start},{end})'"
        )

        drawtext_filters.append(drawtext)

    # Chain all drawtext filters together
    filter_complex = ",".join(drawtext_filters)

    print("\nProcessing video with text overlays...")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vf",
        filter_complex,
        "-c:a",
        "copy",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        output_file,
    ]

    run_ffmpeg(cmd)
    print(f"\n✓ Done! Output: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: process_text.py INPUT OUTPUT")
        print("Example: process_text.py edited.mp4 with_text.mp4")
        print("\nApplies all text overlays from text_marker.py")
        sys.exit(1)

    process_text_overlays(sys.argv[1], sys.argv[2])
