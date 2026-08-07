#!/usr/bin/env python3
"""
Join multiple video clips into one. Fast stream-copy when codecs match,
re-encodes when they don't.

Usage:
    join.py clip1.mp4 clip2.mp4 clip3.mp4 -o output.mp4
    join.py --latest -o output.mp4              # join latest screen recordings
    join.py clips/*.mp4                         # auto-named output
"""

import sys
import os
import glob
from utils import run_ffmpeg, validate_file, raw_dir, temp_path


def latest_recordings(n=10):
    """Return the N most recent screen recordings."""
    pattern = os.path.join(raw_dir(), "screen_*.mp4")
    files = sorted(glob.glob(pattern))
    return files[-n:]


def auto_output(clips):
    """Auto-name output from the first clip."""
    stem = os.path.splitext(os.path.basename(clips[0]))[0]
    return f"{stem}_joined.mp4"


def have_same_codecs(clips):
    """Quick check if all clips share the same video codec."""
    import subprocess, json
    codecs = set()
    for c in clips:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
               "-show_streams", c]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            data = json.loads(r.stdout)
            for s in data.get("streams", []):
                if s["codec_type"] == "video":
                    codecs.add(s["codec_name"])
    return len(codecs) <= 1


def join_clips(clips, output_file, force_reencode=False):
    for c in clips:
        validate_file(c)

    print(f"  Joining {len(clips)} clips → {output_file}")
    for c in clips:
        print(f"    {os.path.basename(c)}")

    use_copy = not force_reencode and have_same_codecs(clips)

    if use_copy:
        print("\n  Using stream copy (same codecs detected).")
        concat_file = temp_path(".txt")
        try:
            with open(concat_file, "w") as f:
                for clip in clips:
                    f.write(f"file '{os.path.abspath(clip)}'\n")
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file, "-c", "copy", output_file,
            ]
            run_ffmpeg(cmd)
        finally:
            if os.path.exists(concat_file):
                os.unlink(concat_file)
    else:
        reason = "forced re-encode" if force_reencode else "mismatched codecs"
        print(f"\n  Using re-encode ({reason}).")
        inputs = []
        filter_parts = []
        for i, clip in enumerate(clips):
            inputs.extend(["-i", clip])
            filter_parts.append(f"[{i}:v][{i}:a]")

        filter_str = "".join(filter_parts) + f"concat=n={len(clips)}:v=1:a=1[v][a]"
        cmd = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_str,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", output_file,
        ]
        run_ffmpeg(cmd)

    size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\n  ✓ Output: {output_file} ({size:.1f} MB)")


if __name__ == "__main__":
    from parser import parse

    ns = parse(
        sys.argv[1:],
        flags=("--reencode", "--latest"),
        doc=__doc__,
    )

    clips = list(ns.positionals)
    output_file = ns.output
    force_reencode = "--reencode" in ns.values

    if "--latest" in ns.values:
        clips = latest_recordings(10)

    if len(clips) < 2:
        print(__doc__.strip())
        print("\nNeed at least 2 clips to join.")
        sys.exit(1)

    if output_file is None:
        output_file = auto_output(clips)

    join_clips(clips, output_file, force_reencode)
