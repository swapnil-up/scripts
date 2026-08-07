#!/usr/bin/env python3
"""
Auto-trim: detect and remove silent pauses to make a tight, snappy edit.
Uses ffmpeg's silencedetect filter; no manual cutting needed.

Usage:
    silence_trim.py input.mp4                       # → input_tight.mp4
    silence_trim.py input.mp4 -o out.mp4 --noise -30dB --min-sil 0.5 --pad 0.25
    silence_trim.py input.mp4 --fast                # stream-copy (keyframe aligned)
    silence_trim.py input.mp4 --hw vaapi            # re-encode via hardware encoder

Markers are saved to ~/vedit/<stem>.markers.json (same format as cut_marker.py),
so you can inspect/edit them with the interactive suite afterwards.
"""

import sys
import os
import subprocess
from utils import (
    validate_file,
    auto_output_path,
    format_time,
    get_duration,
    log,
    log_init,
)
from sidecar import markers_path, save_json

MARKER_EXT = "markers.json"


def parse_silencedetect(stderr):
    """Pure parse of ffmpeg's silencedetect stderr into [(start, end), ...]."""
    intervals = []
    start = None
    for line in (stderr or "").splitlines():
        if "silence_start" in line:
            try:
                start = float(line.split("silence_start:")[1].strip())
            except (IndexError, ValueError):
                start = None
        elif "silence_end" in line:
            try:
                end = float(line.split("silence_end:")[1].strip().split()[0])
            except (IndexError, ValueError):
                continue
            if start is not None:
                intervals.append((start, end))
                start = None
    return intervals


def detect_silence(input_file, noise="-30dB", min_silence=0.5):
    """Run silencedetect and return [(start, end), ...] silence intervals."""
    cmd = [
        "ffmpeg", "-hide_banner", "-i", input_file,
        "-af", f"silencedetect=noise={noise}:d={min_silence}",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running silencedetect: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return parse_silencedetect(result.stderr)


def build_markers(silence, duration, pad=0.25):
    """Expand silence intervals by pad and clip to video bounds, in pairs."""
    markers = []
    for start, end in silence:
        s = max(0.0, start - pad)
        e = min(duration, end + pad)
        if e - s > 0.1:
            markers.append(s)
            markers.append(e)
    return markers


def silence_trim(input_file, output_file, noise="-30dB", min_silence=0.5,
                 pad=0.25, fast=False, hw=None):
    validate_file(input_file)
    duration = get_duration(input_file)
    log(f"silence_trim input={input_file} noise={noise} min_silence={min_silence} pad={pad} fast={fast} hw={hw}")

    print(f"  Detecting silence in {os.path.basename(input_file)} ({duration:.1f}s)...")
    print(f"    noise={noise} min_silence={min_silence}s padding={pad}s")

    silence = detect_silence(input_file, noise, min_silence)
    if not silence:
        print("  No silence detected — nothing to trim.")
        log("silence_trim: no silence found")
        return False

    kept = duration - sum(e - s for s, e in silence)
    print(f"  Found {len(silence)} silent pause(s) — {sum(e - s for s, e in silence):.1f}s removable "
          f"({sum(e - s for s, e in silence) / duration * 100:.0f}%), {kept:.1f}s would remain.")

    markers = build_markers(silence, duration, pad)
    markers_file = markers_path(input_file)
    save_json(markers_file, markers)
    log(f"silence_trim markers={markers_file} n={len(markers)}")

    print(f"\n  Saved {len(markers)} cut markers to {markers_file}")
    print("  Removing marked sections...")

    # Invoke the cut Stage through its canonical CLI seam (not an in-process
    # import), so it gets the same log/exit behaviour and the same `fast`
    # default as every other caller. The CLI defaults to stream-copy; pass
    # `--precise` when this Stage wants a frame-accurate re-encode.
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "process_cuts.py")
    cmd = [sys.executable, script, input_file]
    if output_file:
        cmd += ["-o", output_file]
    if hw:
        cmd += ["--hw", hw]
    if not fast:
        cmd += ["--precise"]
    print(f"  >>> {' '.join(cmd)}")
    if subprocess.call(cmd) != 0:
        log(f"FAIL: process_cuts returned nonzero for {input_file}")
        sys.exit(1)

    log(f"silence_trim done output={output_file}")
    return True


if __name__ == "__main__":
    from parser import parse

    log_init("silence_trim.py")

    ns = parse(
        sys.argv[1:],
        flags=("--fast",),
        options={
            "--noise": str,
            "--min-sil": float,
            "--pad": float,
            "--hw": str,
        },
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
        output_file = auto_output_path(input_file, "tight")

    silence_trim(
        input_file,
        output_file,
        ns.values.get("--noise", "-30dB"),
        ns.values.get("--min-sil", 0.5),
        ns.values.get("--pad", 0.25),
        "--fast" in ns.values,
        ns.values.get("--hw"),
    )
