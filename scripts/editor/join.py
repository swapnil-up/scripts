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
import tempfile
from utils import run_ffmpeg, validate_file, get_vedit_dir


def latest_recordings(n=10):
    """Return the N most recent screen recordings."""
    pattern = os.path.join(get_vedit_dir(), "screen_*.mp4")
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
        concat_file = tempfile.mktemp(suffix=".txt")
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
    clips = []
    output_file = None
    force_reencode = False
    use_latest = False
    n_latest = 10

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "-o" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        elif arg == "--reencode":
            force_reencode = True
            i += 1
        elif arg == "--latest":
            use_latest = True
            i += 1
        elif arg.startswith("--"):
            print(f"  Unknown option: {arg}")
            sys.exit(1)
        else:
            clips.append(arg)
            i += 1

    if use_latest:
        clips = latest_recordings(n_latest)

    if len(clips) < 2:
        print(__doc__.strip())
        print("\nNeed at least 2 clips to join.")
        sys.exit(1)

    if output_file is None:
        output_file = auto_output(clips)

    join_clips(clips, output_file, force_reencode)
