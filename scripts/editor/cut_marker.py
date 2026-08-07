#!/usr/bin/env python3
import sys
import subprocess
import os
from utils import format_time, sidecar_path
from sidecar import markers_path, load_or_reset, fmt_pairs, save_json


def mark_cuts(input_file):
    """
    Open video in mpv, let user mark cut points.
    Marks come in pairs — each pair defines a section to CUT OUT.

    Controls:
      m          - Mark cut point
      [ / ]      - Decrease/increase speed
      LEFT/RIGHT - Seek backward/forward 5s
      UP/DOWN    - Seek backward/forward 60s
      SPACE      - Pause/play
      q          - Quit and save markers

    Sidecar saved to: ~/vedit/<stem>.markers.json
    """

    markers_file = markers_path(input_file)
    timestamp_file = sidecar_path(input_file, "timestamps.tmp")

    markers, cancelled = load_or_reset(markers_file, "cut markers")
    if cancelled:
        return

    print(f"\nMarking cuts for: {input_file}")
    print(f"Sidecar: {markers_file}")
    print("\nControls:")
    print("  m          - Mark cut point")
    print("  [ / ]      - Decrease/increase speed")
    print("  LEFT/RIGHT - Seek backward/forward 5s")
    print("  UP/DOWN    - Seek backward/forward 60s")
    print("  SPACE      - Pause/play")
    print("  q          - Quit and save markers\n")

    if markers:
        print("Existing markers:")
        for i, m in enumerate(markers, 1):
            print(f"  {i}. {format_time(m)}")
        print()

    lua_script = f"""
    markers = {{}}

    function mark_timestamp()
        local time = mp.get_property_number("time-pos")
        table.insert(markers, time)
        mp.osd_message(string.format("Marked: %.2fs (Total: %d marks)", time, #markers), 2)
    end

    function save_and_quit()
        local file = io.open("{timestamp_file}", "w")
        for i, time in ipairs(markers) do
            file:write(string.format("%.3f\\n", time))
        end
        file:close()
        mp.osd_message("Saved " .. #markers .. " markers", 2)
        mp.command("quit")
    end

    mp.add_key_binding("m", "mark", mark_timestamp)
    mp.add_key_binding("q", "save_quit", save_and_quit)
    """

    lua_file = f"/tmp/mpv_marker_{os.getpid()}.lua"
    with open(lua_file, "w") as f:
        f.write(lua_script)

    cmd = ["mpv", "--speed=2", "--osd-level=3", f"--script={lua_file}", input_file]

    try:
        subprocess.run(cmd)

        if os.path.exists(timestamp_file):
            with open(timestamp_file, "r") as f:
                new_markers = [float(line.strip()) for line in f if line.strip()]

            markers.extend(new_markers)
            markers.sort()

            save_json(markers_file, markers)

            os.remove(timestamp_file)

            print(f"\nSaved {len(markers)} total markers to {markers_file}")
            print("\nMarkers:")
            for i, m in enumerate(markers, 1):
                print(f"  {i}. {format_time(m)}")

            pairs = fmt_pairs(markers)
            if pairs:
                print("\nSections to CUT OUT:")
                for i, (start_m, end_m) in enumerate(pairs):
                    duration = end_m - start_m
                    print(
                        f"  Cut {i + 1}: {format_time(start_m)} -> {format_time(end_m)} ({duration:.1f}s)"
                    )
            else:
                print("\nWARNING: Odd number of markers — they must come in pairs.")
                print("Run cut_marker.py again to add the missing marker.")

    finally:
        if os.path.exists(lua_file):
            os.remove(lua_file)


if __name__ == "__main__":
    from parser import parse

    ns = parse(sys.argv[1:], doc=None)
    if not ns.positionals:
        print("Usage: cut_marker.py INPUT_VIDEO")
        print("Example: cut_marker.py raw_workout.mp4")
        print("\nOpens video in mpv. Press 'm' to mark cut points in pairs.")
        print("Each pair defines a section to remove.")
        print("Sidecar saved to ~/vedit/<stem>.markers.json")
        sys.exit(1)

    mark_cuts(ns.positionals[0])
