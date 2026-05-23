#!/usr/bin/env python3
import sys
import json
import os
import tempfile
from utils import (
    run_ffmpeg,
    validate_file,
    get_duration,
    format_time,
    sidecar_path,
    auto_output_path,
    log,
    log_init,
)


def process_marked_cuts(input_file, output_file, fast=True):
    """
    Remove all sections defined by markers from cut_marker.py.

    Reads:  ~/vedit/<stem>.markers.json
    Output: next to input as <stem>_cut.mp4  (or explicit OUTPUT arg)
    """
    validate_file(input_file)

    markers_file = sidecar_path(input_file, "markers.json")
    if not os.path.exists(markers_file):
        log(f"FAIL: no markers file at {markers_file}")
        print(f"Error: No markers file found at {markers_file}")
        print("Run cut_marker.py first to create markers.")
        sys.exit(1)

    with open(markers_file, "r") as f:
        markers = json.load(f)

    log(f"input={input_file} output={output_file} fast={fast}")
    log(f"markers_file={markers_file} n_markers={len(markers)}")
    log(f"raw_markers={markers}")

    if len(markers) == 0:
        log("FAIL: empty markers")
        print("No markers found. Nothing to cut.")
        sys.exit(1)

    if len(markers) % 2 != 0:
        log(f"FAIL: odd markers ({len(markers)})")
        print(
            f"ERROR: Odd number of markers ({len(markers)}). Each cut needs a start AND end."
        )
        print("Run cut_marker.py again to add the missing marker.")
        sys.exit(1)

    duration = get_duration(input_file)
    log(f"input_duration={duration:.3f}s")

    segments = []
    last_end = 0

    print("Cutting out:")
    for i in range(0, len(markers), 2):
        cut_start = markers[i]
        cut_end = markers[i + 1]
        print(
            f"  Section {i // 2 + 1}: {format_time(cut_start)} -> {format_time(cut_end)}"
        )
        if cut_start > last_end:
            segments.append((last_end, cut_start))
        last_end = cut_end

    if last_end < duration:
        segments.append((last_end, duration))

    log(f"segments_to_keep={[(round(s,3), round(e,3), round(e-s,3)) for s,e in segments]}")

    print(f"\nKeeping {len(segments)} segment(s)")

    if len(segments) == 0:
        log("FAIL: no segments to keep")
        print("ERROR: All video would be cut out!")
        sys.exit(1)

    temp_clips = []
    codec = ["-c", "copy"] if fast else ["-c:v", "libx264", "-preset", "fast"]

    try:
        for i, (start, end) in enumerate(segments):
            temp_file = tempfile.mktemp(suffix=".mp4")
            temp_clips.append(temp_file)
            print(f"Processing segment {i + 1}/{len(segments)}...")
            cmd = (
                ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", input_file]
                + codec
                + [temp_file]
            )
            log(f"ffmpeg_segment_{i+1}: {' '.join(str(c) for c in cmd)}")
            run_ffmpeg(cmd)

        print("Joining segments...")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for clip in temp_clips:
                f.write(f"file '{os.path.abspath(clip)}'\n")
            concat_file = f.name

        cmd = (
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file]
            + codec
            + [output_file]
        )
        log(f"ffmpeg_concat: {' '.join(str(c) for c in cmd)}")
        run_ffmpeg(cmd)
        os.unlink(concat_file)

        kept_duration = sum(end - start for start, end in segments)
        cut_duration = duration - kept_duration

        log(f"done: kept={kept_duration:.3f}s cut={cut_duration:.3f}s output={output_file}")

        print(f"\n✓ Output: {output_file}")
        print(f"\nSummary:")
        print(f"  Original : {format_time(duration)}")
        print(
            f"  Cut out  : {format_time(cut_duration)} ({cut_duration / duration * 100:.1f}%)"
        )
        print(f"  Final    : {format_time(kept_duration)}")

    finally:
        for clip in temp_clips:
            if os.path.exists(clip):
                os.unlink(clip)


if __name__ == "__main__":
    log_init("process_cuts.py")
    if len(sys.argv) < 2:
        print("Usage: process_cuts.py INPUT [OUTPUT] [--precise]")
        print("Example: process_cuts.py raw_workout.mp4")
        print("         process_cuts.py raw_workout.mp4 custom_out.mp4")
        print("\nReads markers from ~/vedit/<stem>.markers.json")
        print("Output defaults to <input_dir>/<stem>_cut.mp4")
        sys.exit(1)

    input_file = sys.argv[1]

    # Determine output — explicit arg or auto-generated
    explicit = [a for a in sys.argv[2:] if not a.startswith("--")]
    output_file = explicit[0] if explicit else auto_output_path(input_file, "cut")

    fast = "--precise" not in sys.argv
    process_marked_cuts(input_file, output_file, fast)
