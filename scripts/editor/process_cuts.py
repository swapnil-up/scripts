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
    auto_output_path,
    temp_path,
    log,
    log_init,
)
from encoder import resolve
from sidecar import markers_path, pair_cut_markers


def _encode_flags(fast, hw, crf):
    """Return the ffmpeg flags to use for segment + concat encoding."""
    if fast:
        return ["-c", "copy"], []
    enc = resolve(hw)
    fmt = enc.filter()
    vf = ["-vf", fmt] if fmt else []
    codec = ["-c:a", "aac", "-b:a", "192k"] + enc.flags(crf)
    codec = enc.init_flags() + codec
    return codec, vf


def process_marked_cuts(input_file, output_file, fast=True, hw=None, crf=23):
    """
    Remove all sections defined by markers from cut_marker.py.

    Reads:  ~/vedit/<stem>.markers.json
    Output: next to input as <stem>_cut.mp4  (or explicit OUTPUT arg)
    """
    validate_file(input_file)

    markers_file = markers_path(input_file)
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

    duration = get_duration(input_file)
    log(f"input_duration={duration:.3f}s")

    try:
        segments = pair_cut_markers(markers, duration)
    except ValueError as e:
        log(f"FAIL: {e}")
        print(f"ERROR: {e}")
        print("Run cut_marker.py again to fix the markers.")
        sys.exit(1)

    pairs = [(markers[i], markers[i + 1]) for i in range(0, len(markers), 2)]
    print("Cutting out:")
    for i, (cut_start, cut_end) in enumerate(pairs):
        print(
            f"  Section {i + 1}: {format_time(cut_start)} -> {format_time(cut_end)}"
        )

    log(f"segments_to_keep={[(round(s,3), round(e,3), round(e-s,3)) for s,e in segments]}")

    print(f"\nKeeping {len(segments)} segment(s)")

    temp_clips = []
    codec, vf = _encode_flags(fast, hw, crf)

    try:
        for i, (start, end) in enumerate(segments):
            temp_file = temp_path(".mp4")
            temp_clips.append(temp_file)
            print(f"Processing segment {i + 1}/{len(segments)}...")
            cmd = (
                ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", input_file]
                + codec
                + vf
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
            + vf
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
    from parser import parse

    log_init("process_cuts.py")

    ns = parse(
        sys.argv[1:],
        flags=("--precise",),
        options={"--hw": str, "--crf": int},
        doc=(
            "Usage: process_cuts.py INPUT [OUTPUT] [--precise] [--hw vaapi] [--crf N]\n"
            "Example: process_cuts.py raw_workout.mp4\n"
            "         process_cuts.py raw_workout.mp4 custom_out.mp4\n\n"
            "Reads markers from ~/vedit/<stem>.markers.json\n"
            "Output defaults to <input_dir>/<stem>_cut.mp4"
        ),
    )

    if not ns.positionals:
        print("Usage: process_cuts.py INPUT [OUTPUT] [--precise] [--hw vaapi] [--crf N]")
        print("Example: process_cuts.py raw_workout.mp4")
        print("         process_cuts.py raw_workout.mp4 custom_out.mp4")
        print("\nReads markers from ~/vedit/<stem>.markers.json")
        print("Output defaults to <input_dir>/<stem>_cut.mp4")
        sys.exit(1)

    input_file = ns.positionals[0]
    output_file = ns.output
    if len(ns.positionals) > 1:
        output_file = ns.positionals[1]
    if output_file is None:
        output_file = auto_output_path(input_file, "cut")

    fast = "--precise" not in ns.values
    hw = ns.values.get("--hw")
    crf = ns.values.get("--crf", 23)
    process_marked_cuts(input_file, output_file, fast, hw, crf)
