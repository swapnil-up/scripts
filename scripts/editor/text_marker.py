#!/usr/bin/env python3
import sys
import subprocess
import os
from utils import format_time, sidecar_path
from sidecar import texts_path, load_or_reset, save_json


def mark_text_overlays(input_file):
    """
    Open video in mpv, let user mark text overlays with timing
    Controls:
    - 't' to add text at current timestamp
    - space to pause/play
    - arrow keys to seek
    - q to quit and save
    """

    texts_file = texts_path(input_file)

    # Check if texts already exist
    text_overlays, cancelled = load_or_reset(texts_file, "text overlays")
    if cancelled:
        return

    print(f"\nAdding text overlays to: {input_file}")
    print("Controls:")
    print("  t - Add text overlay at current position")
    print("  [ / ] - Decrease/increase speed")
    print("  LEFT/RIGHT - Seek backward/forward 5s")
    print("  SPACE - Pause/play")
    print("  q - Quit and save\n")

    if text_overlays:
        print("Existing text overlays:")
        for i, overlay in enumerate(text_overlays, 1):
            print(
                f"  {i}. {format_time(overlay['start'])} -> {format_time(overlay['end'])}: \"{overlay['text']}\" ({overlay.get('position', 'bottom')})"
            )
        print()

    # MPV lua script to capture timestamps when 't' is pressed
    timestamp_file = sidecar_path(input_file, "text_timestamps.tmp")
    lua_script = f"""
    function add_text_overlay()
        local time = mp.get_property_number("time-pos")
        local file = io.open("{timestamp_file}", "a")
        file:write(string.format("%.3f\\n", time))
        file:close()
        mp.osd_message(string.format("Text marker at: %.2fs", time), 2)
    end
    
    mp.add_key_binding("t", "add_text", add_text_overlay)
    """

    lua_file = f"/tmp/mpv_text_marker_{os.getpid()}.lua"
    with open(lua_file, "w") as f:
        f.write(lua_script)

    # Run mpv
    cmd = ["mpv", "--osd-level=3", f"--script={lua_file}", input_file]

    try:
        subprocess.run(cmd)

        # Read timestamps
        timestamp_file = sidecar_path(input_file, "text_timestamps.tmp")
        if os.path.exists(timestamp_file):
            with open(timestamp_file, "r") as f:
                new_timestamps = [float(line.strip()) for line in f if line.strip()]

            # For each timestamp, ask for text details
            for ts in new_timestamps:
                print(f"\n--- Text at {format_time(ts)} ---")
                text = input("Text to display: ").strip()
                if not text:
                    print("Skipping (no text entered)")
                    continue

                duration_input = input("Duration in seconds (default: 3): ").strip()
                duration = float(duration_input) if duration_input else 3.0

                position = (
                    input("Position - top/center/bottom (default: bottom): ")
                    .strip()
                    .lower()
                )
                if position not in ["top", "center", "bottom"]:
                    position = "bottom"

                fontsize_input = input("Font size (default: 48): ").strip()
                fontsize = int(fontsize_input) if fontsize_input else 48

                color = input("Color (default: white): ").strip()
                if not color:
                    color = "white"

                text_overlays.append(
                    {
                        "text": text,
                        "start": ts,
                        "end": ts + duration,
                        "position": position,
                        "fontsize": fontsize,
                        "color": color,
                    }
                )

            # Sort by start time
            text_overlays.sort(key=lambda x: x["start"])

            # Save
            save_json(texts_file, text_overlays)

            os.remove(timestamp_file)

            print(f"\n✓ Saved {len(text_overlays)} text overlays to {texts_file}")
            print("\nAll text overlays:")
            for i, overlay in enumerate(text_overlays, 1):
                duration = overlay["end"] - overlay["start"]
                print(
                    f"  {i}. {format_time(overlay['start'])} ({duration}s): \"{overlay['text']}\" - {overlay['position']}, size {overlay['fontsize']}"
                )

    finally:
        if os.path.exists(lua_file):
            os.remove(lua_file)


if __name__ == "__main__":
    from parser import parse

    ns = parse(sys.argv[1:], doc=None)
    if not ns.positionals:
        print("Usage: text_marker.py INPUT_VIDEO")
        print("Example: text_marker.py edited_workout.mp4")
        print("\nOpens video in mpv. Press 't' at each point you want text to appear.")
        print(
            "After closing mpv, you'll be prompted to enter text details for each marker."
        )
        sys.exit(1)

    mark_text_overlays(ns.positionals[0])
