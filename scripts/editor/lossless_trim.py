#!/usr/bin/env python3
"""
Lossless trimmer: cut a section from a video instantly with -c copy,
preserving 100% quality (no re-encode). Great for trimming raw GoPro
footage before processing.

Usage:
    lossless_trim.py input.mp4 --start 10 --end 90 -o out.mp4
    lossless_trim.py input.mp4 --start 00:01:30 -o out.mp4       # keep from 1:30 to end
    lossless_trim.py input.mp4 --end 5:00 -o out.mp4             # first 5 minutes
"""

import sys
import os
import subprocess
from utils import validate_file, auto_output_path, parse_time, format_time, run_ffmpeg


def lossless_trim(input_file, output_file, start=None, end=None):
    validate_file(input_file)

    duration = None
    from utils import get_duration
    total = get_duration(input_file)

    start_s = parse_time(start) if start else 0
    end_s = parse_time(end) if end else total

    if start_s >= end_s:
        print(f"Error: start ({format_time(start_s)}) must be before end ({format_time(end_s)})")
        sys.exit(1)

    cmd = ["ffmpeg", "-y"]
    if start_s:
        cmd += ["-ss", str(start_s)]
    if end_s:
        cmd += ["-to", str(end_s)]
    cmd += ["-i", input_file, "-c", "copy", "-avoid_negative_ts", "make_zero", output_file]
    print(f"  Trimming (lossless, -c copy):")
    print(f"    {format_time(start_s)} → {format_time(end_s)}  ({(end_s - start_s):.1f}s of {format_time(total)})")
    run_ffmpeg(cmd)

    size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\n  ✓ Output: {output_file} ({size:.1f} MB) — no re-encode, quality preserved.")


if __name__ == "__main__":
    from parser import parse

    ns = parse(
        sys.argv[1:],
        options={"--start": str, "--end": str},
        doc=__doc__,
    )

    if not ns.positionals:
        print(__doc__)
        sys.exit(1)

    input_file = ns.positionals[0]
    output_file = ns.output
    if len(ns.positionals) > 1:
        output_file = ns.positionals[1]
    if output_file is None:
        output_file = auto_output_path(input_file, "trimmed")

    lossless_trim(input_file, output_file, ns.values.get("--start"), ns.values.get("--end"))
